#include "precompiled.h"
#pragma hdrstop

#include "SignalRoom.h"
#include "../renderer/RenderCommon.h"
#include "../renderer/ModelManager.h"
#include "../renderer/GLState.h"
#include "../libs/imgui/imgui.h"

#include <array>

bool R_WriteRendererEvidence( const char* filename );

namespace
{
constexpr float ROOM_LENGTH = 768.0f;
constexpr float ROOM_HALF_WIDTH = 280.0f;
constexpr float ROOM_HEIGHT = 160.0f;
constexpr float PLAYER_RADIUS = 12.0f;
constexpr float PLAYER_SPEED = 176.0f;

const idBounds obstacles[] =
{
	idBounds( idVec3( 252, -52, 0 ), idVec3( 310, 52, 112 ) ),
	idBounds( idVec3( 486, 36, 0 ), idVec3( 548, 90, 88 ) ),
	idBounds( idVec3( 438, -176, 0 ), idVec3( 510, -110, 120 ) )
};
const idVec2 modulePositions[] = { idVec2( 100, 118 ), idVec2( 350, 118 ), idVec2( 590, 118 ) };
constexpr size_t MODULE_COUNT = sizeof( modulePositions ) / sizeof( modulePositions[0] );

bool quitRequested;

void QuitSignalRoom_f( const idCmdArgs& )
{
	quitRequested = true;
}

bool CanOccupy( const idVec2& position )
{
	if( position.x < PLAYER_RADIUS || position.x > ROOM_LENGTH - PLAYER_RADIUS ||
		position.y < -ROOM_HALF_WIDTH + PLAYER_RADIUS || position.y > ROOM_HALF_WIDTH - PLAYER_RADIUS )
	{
		return false;
	}
	for( const idBounds& obstacle : obstacles )
	{
		if( position.x >= obstacle[0].x - PLAYER_RADIUS && position.x <= obstacle[1].x + PLAYER_RADIUS &&
			position.y >= obstacle[0].y - PLAYER_RADIUS && position.y <= obstacle[1].y + PLAYER_RADIUS )
		{
			return false;
		}
	}
	return true;
}

class SignalRoom
{
public:
	explicit SignalRoom( const idMaterial* material );
	~SignalRoom();
	void Reset();
	void Step( const std::array<bool, K_LAST_KEY>& held, float seconds );
	void Draw( int now, float seconds );

private:
	qhandle_t AddBox( const idVec3& min, const idVec3& max, const idVec4& color );
	void DrawHud( float seconds ) const;

	idRenderWorld* world;
	const idMaterial* material;
	idList<idRenderModel*> models;
	std::array<qhandle_t, MODULE_COUNT> modules;
	std::array<bool, MODULE_COUNT> recovered = {};
	idVec2 position;
	float yaw = 0.0f;
	int collected = 0;
	int frameWidth = 0;
	int frameHeight = 0;
	bool won = false;
	bool loggedCollision = false;
};

SignalRoom::SignalRoom( const idMaterial* material )
	: world( renderSystem->AllocRenderWorld() ), material( material )
{
	world->InitFromMap( nullptr );
	const idVec4 wall( 0.26f, 0.39f, 0.46f, 1.0f );
	const idVec4 trim( 0.12f, 0.70f, 0.73f, 1.0f );
	const idVec4 floor[2] = { idVec4( 0.17f, 0.23f, 0.27f, 1.0f ), idVec4( 0.21f, 0.28f, 0.31f, 1.0f ) };
	for( int x = 0; x < 6; ++x )
	{
		for( int y = 0; y < 4; ++y )
		{
			const float left = x * 128.0f;
			const float lateralEdge = -ROOM_HALF_WIDTH + y * 140.0f;
			AddBox( idVec3( left, lateralEdge, -8 ), idVec3( left + 127, lateralEdge + 139, 0 ), floor[( x + y ) % 2] );
		}
	}
	AddBox( idVec3( -8, -288, -12 ), idVec3( 776, 288, -8 ), wall );
	AddBox( idVec3( -8, -288, 0 ), idVec3( 0, 288, ROOM_HEIGHT ), wall );
	AddBox( idVec3( ROOM_LENGTH, -288, 0 ), idVec3( 776, 288, ROOM_HEIGHT ), wall );
	AddBox( idVec3( 0, -288, 0 ), idVec3( ROOM_LENGTH, -ROOM_HALF_WIDTH, ROOM_HEIGHT ), wall );
	AddBox( idVec3( 0, ROOM_HALF_WIDTH, 0 ), idVec3( ROOM_LENGTH, 288, ROOM_HEIGHT ), wall );
	AddBox( idVec3( 0, -280, ROOM_HEIGHT ), idVec3( 768, 280, 168 ), idVec4( 0.15f, 0.22f, 0.29f, 1 ) );
	for( const float edge : { -279.0f, 277.0f } )
	{
		AddBox( idVec3( 2, edge, 99 ), idVec3( 766, edge + 2, 103 ), trim );
	}
	for( const idBounds& obstacle : obstacles )
	{
		AddBox( obstacle[0], obstacle[1], idVec4( 0.52f, 0.32f, 0.19f, 1 ) );
		const idVec3& top = obstacle[1];
		AddBox( idVec3( obstacle[0].x, obstacle[0].y, top.z ),
				idVec3( top.x, top.y, top.z + 3 ), idVec4( 0.98f, 0.58f, 0.26f, 1 ) );
	}
	for( size_t index = 0; index < modules.size(); ++index )
	{
		const idVec2& point = modulePositions[index];
		AddBox( idVec3( point.x - 19, point.y - 19, 0 ), idVec3( point.x + 19, point.y + 19, 2 ), trim );
		modules[index] = AddBox( idVec3( point.x - 10, point.y - 10, 40 ),
								idVec3( point.x + 10, point.y + 10, 72 ), idVec4( 0.14f, 0.95f, 0.97f, 1 ) );
	}
	AddBox( idVec3( 660, -156, 0 ), idVec3( 767, -76, 2 ), idVec4( 0.33f, 0.52f, 0.43f, 1 ) );
	for( const float y : { -156.0f, -84.0f } )
	{
		AddBox( idVec3( ROOM_LENGTH - 4, y, 0 ), idVec3( ROOM_LENGTH, y + 8, 106 ), trim );
	}
	AddBox( idVec3( ROOM_LENGTH - 5, -153, 99 ), idVec3( ROOM_LENGTH - 1, -79, 108 ), idVec4( 0.95f, 0.54f, 0.26f, 1 ) );
	Reset();
}

SignalRoom::~SignalRoom()
{
	renderSystem->FreeRenderWorld( world );
	for( idRenderModel* model : models )
	{
		renderModelManager->FreeModel( model );
	}
}

qhandle_t SignalRoom::AddBox( const idVec3& min, const idVec3& max, const idVec4& color )
{
	const idVec3 points[] =
	{
		idVec3( min.x, min.y, min.z ), idVec3( max.x, min.y, min.z ),
		idVec3( max.x, max.y, min.z ), idVec3( min.x, max.y, min.z ),
		idVec3( min.x, min.y, max.z ), idVec3( max.x, min.y, max.z ),
		idVec3( max.x, max.y, max.z ), idVec3( min.x, max.y, max.z )
	};
	const int faces[6][4] = { { 0, 1, 2, 3 }, { 4, 7, 6, 5 }, { 0, 4, 5, 1 },
							 { 3, 2, 6, 7 }, { 0, 3, 7, 4 }, { 1, 5, 6, 2 } };
	const float shade[6] = { 0.70f, 1.0f, 0.76f, 0.87f, 0.69f, 0.94f };
	const idVec2 uv[] = { idVec2( 0, 0 ), idVec2( 1, 0 ), idVec2( 1, 1 ), idVec2( 0, 1 ) };
	const int indices[] = { 0, 1, 2, 0, 2, 3 };
	srfTriangles_t* triangles = R_AllocStaticTriSurf();
	R_AllocStaticTriSurfVerts( triangles, 24 );
	R_AllocStaticTriSurfIndexes( triangles, 36 );
	triangles->numVerts = 24;
	triangles->numIndexes = 36;
	triangles->generateNormals = true;
	for( int face = 0; face < 6; ++face )
	{
		const auto colorBytes = PackColor( idVec4( color.x * shade[face], color.y * shade[face], color.z * shade[face], color.w ) );
		for( int corner = 0; corner < 4; ++corner )
		{
			auto& vertex = triangles->verts[face * 4 + corner];
			vertex.Clear();
			vertex.xyz = points[faces[face][corner]];
			vertex.SetTexCoord( uv[corner].x, uv[corner].y );
			vertex.SetColor( colorBytes );
		}
		for( int index = 0; index < 6; ++index )
		{
			triangles->indexes[face * 6 + index] = face * 4 + indices[index];
		}
	}
	idRenderModel* model = renderModelManager->AllocModel();
	model->InitEmpty( "signal_room_box" );
	model->AddSurface( { 0, material, triangles } );
	model->FinishSurfaces( false );
	models.Append( model );

	renderEntity_t entity = {};
	entity.origin = vec3_origin;
	entity.axis = mat3_identity;
	entity.hModel = model;
	entity.noShadow = true;
	for( int channel = SHADERPARM_RED; channel <= SHADERPARM_ALPHA; ++channel )
	{
		entity.shaderParms[channel] = 1;
	}
	return world->AddEntityDef( &entity );
}

void SignalRoom::Reset()
{
	for( size_t index = 0; index < modules.size(); ++index )
	{
		if( recovered[index] )
		{
			renderEntity_t entity = *world->GetRenderEntity( modules[index] );
			entity.origin.z = 0;
			world->UpdateEntityDef( modules[index], &entity );
		}
	}
	recovered.fill( false );
	position.Set( 100, 0 );
	yaw = 0.0f;
	collected = 0;
	won = false;
	loggedCollision = false;
	Sys_Printf( "Signal Room: reset\n" );
}

void SignalRoom::Step( const std::array<bool, K_LAST_KEY>& held, float seconds )
{
	if( won )
	{
		return;
	}
	yaw = idMath::AngleNormalize180( yaw + 125.0f * seconds * ( int( held[K_LEFTARROW] ) - int( held[K_RIGHTARROW] ) ) );
	const idMat3 axis = idAngles( 0, yaw, 0 ).ToMat3();
	idVec2 movement = axis[0].ToVec2() * float( int( held[K_W] || held[K_UPARROW] ) - int( held[K_S] || held[K_DOWNARROW] ) ) +
					  axis[1].ToVec2() * float( int( held[K_A] ) - int( held[K_D] ) );
	if( movement.LengthSqr() > 1.0f )
	{
		movement.Normalize();
	}
	movement *= PLAYER_SPEED * seconds;
	for( int direction = 0; direction < 2; ++direction )
	{
		idVec2 candidate = position;
		candidate[direction] += movement[direction];
		if( CanOccupy( candidate ) )
		{
			position = candidate;
		}
		else if( !loggedCollision )
		{
			Sys_Printf( "Signal Room: movement blocked\n" );
			loggedCollision = true;
		}
	}

	for( size_t index = 0; index < modules.size(); ++index )
	{
		if( recovered[index] || ( position - modulePositions[index] ).LengthSqr() > 28.0f * 28.0f )
		{
			continue;
		}
		renderEntity_t module = *world->GetRenderEntity( modules[index] );
		module.origin.z = -200;
		world->UpdateEntityDef( modules[index], &module );
		recovered[index] = true;
		++collected;
		Sys_Printf( "Signal Room: module %d/%d collected\n", collected, int( MODULE_COUNT ) );
	}

	if( position.x >= 660 && position.y >= -156 && position.y <= -76 && collected == MODULE_COUNT )
	{
		won = true;
		Sys_Printf( "Signal Room: exit reached\n" );
	}
}

void SignalRoom::DrawHud( float seconds ) const
{
	ImGuiIO& io = ImGui::GetIO();
	const float width = float( renderSystem->GetWidth() );
	const float height = float( renderSystem->GetHeight() );
	io.IniFilename = nullptr;
	io.DisplaySize = ImVec2( width, height );
	io.DeltaTime = idMath::ClampFloat( 0.001f, 0.05f, seconds );
	ImGui::NewFrame();
	ImDrawList* hud = ImGui::GetForegroundDrawList();
	hud->AddRectFilled( ImVec2( 12, 12 ), ImVec2( 302, 69 ), IM_COL32( 9, 21, 31, 220 ), 7 );
	hud->AddText( nullptr, 17, ImVec2( 25, 20 ), IM_COL32( 225, 248, 249, 255 ), "SIGNAL ROOM" );
	const char* objective = collected == MODULE_COUNT ? "Go to the exit platform" : "Recover the three signal modules";
	hud->AddText( ImVec2( 25, 46 ), IM_COL32( 204, 222, 226, 255 ), objective );
	for( size_t index = 0; index < modules.size(); ++index )
	{
		const float x = 225 + 20 * float( index );
		hud->AddRectFilled( ImVec2( x, 22 ), ImVec2( x + 15, 34 ),
						   int( index ) < collected ? IM_COL32( 32, 223, 207, 255 ) : IM_COL32( 77, 102, 113, 255 ), 3 );
	}
	const ImVec2 center( width * 0.5f, height * 0.5f );
	hud->AddCircle( center, 4, IM_COL32( 228, 241, 243, 210 ), 12, 1 );
	hud->AddRectFilled( ImVec2( 12, height - 39 ), ImVec2( 390, height - 12 ), IM_COL32( 9, 21, 31, 220 ), 6 );
	hud->AddText( ImVec2( 24, height - 32 ), IM_COL32( 221, 238, 240, 255 ), "WASD Move    Left/Right Turn    R Reset    Esc Exit" );
	if( won )
	{
		hud->AddRectFilled( ImVec2( center.x - 127, center.y - 45 ), ImVec2( center.x + 127, center.y + 45 ), IM_COL32( 8, 30, 34, 241 ), 8 );
		hud->AddText( nullptr, 25, ImVec2( center.x - 109, center.y - 30 ), IM_COL32( 105, 245, 209, 255 ), "SIGNAL RESTORED" );
		hud->AddText( ImVec2( center.x - 72, center.y + 11 ), IM_COL32( 217, 240, 240, 255 ), "R Restart    Esc Exit" );
	}
	ImGui::Render();
	renderSystem->SetGLState( GLS_DEPTHFUNC_ALWAYS | GLS_SRCBLEND_SRC_ALPHA | GLS_DSTBLEND_ONE_MINUS_SRC_ALPHA );
	backEnd.ImGui_RenderDrawLists( ImGui::GetDrawData() );
}

void SignalRoom::Draw( int now, float seconds )
{
	const int width = renderSystem->GetWidth();
	const int height = renderSystem->GetHeight();
	if( width <= 0 || height <= 0 )
	{
		return;
	}
	if( width != frameWidth || height != frameHeight )
	{
		// A resize arrives after the previous swap set up the next frame's crop.
		// Discard that empty command buffer and start with the new dimensions.
		renderSystem->SwapCommandBuffers( nullptr, nullptr, nullptr, nullptr, nullptr, nullptr );
		frameWidth = width;
		frameHeight = height;
	}
	renderView_t view = {};
	view.viewID = 1;
	view.vieworg.Set( position.x, position.y, 58 );
	view.vieworg_weapon = view.vieworg;
	view.viewaxis = idAngles( 0, yaw, 0 ).ToMat3();
	view.fov_x = 90.0f;
	view.fov_y = 2.0f * RAD2DEG( idMath::ATan( float( height ) / width ) );
	view.time[0] = view.time[1] = now;
	view.rdflags = RDF_NOSHADOWS | RDF_NOAMBIENT;
	world->RenderScene( &view );
	DrawHud( seconds );
	const emptyCommand_t* commands = renderSystem->SwapCommandBuffers( nullptr, nullptr, nullptr, nullptr, nullptr, nullptr );
	renderSystem->RenderCommandBuffers( commands );
}
}

void RunSignalRoom()
{
	const idMaterial* material = declManager->FindMaterial( "signal_room/solid", false );
	if( !material )
	{
		Sys_Error( "Missing signal_room/solid. Use the Signal Room launcher." );
	}
	globalImages->LoadDeferredImages();
	quitRequested = false;
	cmdSystem->RemoveCommand( "quit" );
	cmdSystem->AddCommand( "quit", QuitSignalRoom_f, CMD_FL_SYSTEM, "exit Signal Room" );

	SignalRoom room( material );
	std::array<bool, K_LAST_KEY> held = {};
	int previous = Sys_Milliseconds();
	room.Draw( previous, 0.016f );
	Sys_Printf( "Signal Room: ready\n" );
	while( !quitRequested )
	{
		Sys_GenerateEvents();
		for( sysEvent_t event = Sys_GetEvent(); event.evType != SE_NONE; event = Sys_GetEvent() )
		{
			if( event.IsKeyEvent() && event.evValue > K_NONE && event.evValue < K_LAST_KEY )
			{
				if( event.IsKeyDown() && !held[event.evValue] )
				{
					if( event.GetKey() == K_ESCAPE )
					{
						quitRequested = true;
					}
					else if( event.GetKey() == K_R )
					{
						room.Reset();
					}
				}
				held[event.evValue] = event.IsKeyDown();
			}
			if( event.evPtr )
			{
				if( event.evType == SE_CONSOLE && idStr::Cmp( static_cast<const char*>( event.evPtr ), "quit" ) == 0 )
				{
					quitRequested = true;
				}
				Mem_Free( event.evPtr );
			}
		}
		cmdSystem->ExecuteCommandBuffer();
		if( quitRequested )
		{
			break;
		}
		if( !cvarSystem->GetCVarBool( "com_activeApp" ) )
		{
			held.fill( false );
		}
		const int now = Sys_Milliseconds();
		const float seconds = idMath::ClampFloat( 0, 0.05f, ( now - previous ) * 0.001f );
		previous = now;
		room.Step( held, seconds );
		room.Draw( now, seconds );
		Sys_Sleep( 8 );
	}
	renderSystem->SwapCommandBuffers( nullptr, nullptr, nullptr, nullptr, nullptr, nullptr );
	if( !R_WriteRendererEvidence( "screenshots/signal-room.png" ) )
	{
		common->Warning( "Could not capture the Signal Room frame" );
	}
}
