#Requires -Version 7.2
param(
    [ValidateSet('Release', 'Debug')]
    [string] $Configuration = 'Release'
)

$ErrorActionPreference = 'Stop'
if (-not $IsWindows) {
    throw 'Windows x64 with Visual Studio 2022 and Windows SDK 10.0.26100.0 is required.'
}

function Get-PinnedZip($Url, $Sha256, $Directory) {
    $Archive = Join-Path $Directory ([IO.Path]::GetFileName($Url))
    if (-not (Test-Path -LiteralPath $Archive)) {
        Invoke-WebRequest -Uri $Url -OutFile "$Archive.download"
        Move-Item -LiteralPath "$Archive.download" -Destination $Archive -Force
    }
    if ((Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash -ne $Sha256) {
        Remove-Item -LiteralPath $Archive
        throw "SHA-256 mismatch for $Url"
    }
    Expand-Archive -LiteralPath $Archive -DestinationPath $Directory -Force
}

Push-Location (Join-Path $PSScriptRoot '..')
try {
    $Tools = Join-Path $PWD 'build-rtcwnextgen-tools'
    New-Item -ItemType Directory -Path $Tools -Force | Out-Null
    Get-PinnedZip 'https://github.com/Kitware/CMake/releases/download/v3.31.6/cmake-3.31.6-windows-x86_64.zip' `
        'd163cd3ab4959b0a53fa8988f2ddbd2e6c501658201e6a154386bad9dbe4f836' $Tools
    Get-PinnedZip 'https://github.com/ispc/ispc/releases/download/v1.26.0/ispc-v1.26.0-windows.zip' `
        'cffe9904d32260994fa264f8fca60eac7be9f8995c122bacf456a1c66ac72987' $Tools
    $Cmake = Join-Path $Tools 'cmake-3.31.6-windows-x86_64/bin/cmake.exe'
    $Ispc = Join-Path $Tools 'ispc-v1.26.0-windows/bin/ispc.exe'
    $SdkRoot = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots').KitsRoot10
    $Dxc = Join-Path $SdkRoot 'bin/10.0.26100.0/x64/dxc.exe'
    if (-not (Test-Path -LiteralPath $Dxc -PathType Leaf)) {
        throw "Install Windows SDK 10.0.26100.0 with its x64 DXC tools. Missing $Dxc"
    }

    git submodule update --init --recursive
    if ($LASTEXITCODE -ne 0) { throw 'Submodule checkout failed.' }
    & $Cmake -S neo -B build-windows -G 'Visual Studio 17 2022' -A 'x64,version=10.0.26100.0' -T 'version=14.44' `
        -DUSE_VULKAN=OFF -DUSE_DX12=ON -DUSE_DXIL_ON_DX12=ON -DSHADERMAKE_FIND_DXC_SPIRV=OFF `
        -DSHADERMAKE_FIND_FXC=OFF "-DDXC_PATH=$Dxc" "-DISPC_EXECUTABLE=$Ispc" `
        -DFFMPEG=OFF -DBINKDEC=ON -DREPRODUCIBLE_BUILD=ON
    if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }
    Select-String -Path 'build-windows/CMakeFiles/*/CMakeCXXCompiler.cmake' -Pattern 'set\(CMAKE_CXX_COMPILER_VERSION '
    & $Dxc --version
    if ($LASTEXITCODE -ne 0) { throw 'DXC version check failed.' }
    $BuildErrors = Join-Path $PWD 'build-windows/compiler-errors.log'
    & $Cmake --build build-windows --config $Configuration --parallel 2 -- /fl "/flp:LogFile=$BuildErrors;ErrorsOnly"
    if ($LASTEXITCODE -ne 0) {
        if ($env:GITHUB_ACTIONS -eq 'true' -and (Test-Path -LiteralPath $BuildErrors)) {
            Get-Content -LiteralPath $BuildErrors |
                Where-Object { $_ -match '\berror\b' } |
                Select-Object -First 8 |
                ForEach-Object { Write-Host "::error::$($_.Trim().Replace('%', '%25'))" }
        }
        throw 'Windows build failed.'
    }
}
finally {
    Pop-Location
}
