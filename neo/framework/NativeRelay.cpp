#include "precompiled.h"
#pragma hdrstop

#include "../d3xp/Game_local.h"
#include "../libs/imgui/imgui.h"
#include "../renderer/GLState.h"
#include "../renderer/ModelManager.h"
#include "../renderer/RenderCommon.h"
#include "../aas/AASFile.h"

#include <array>
#include <memory>

bool R_WriteRendererEvidence( const char* filename );

namespace
{
constexpr const char* RELAY_MAP = "maps/relay";
constexpr int TICK_MS = 16;
constexpr float PLAYER_RADIUS = 16;
constexpr float STAND_HEIGHT = 64;
constexpr float CROUCH_HEIGHT = 36;
constexpr int WALK_FLAGS = TFL_WALK | TFL_AIR;
bool relayQuitRequested;

void RelayQuit_f( const idCmdArgs& )
{
	relayQuitRequested = true;
}

idVec3 RelayOrigin( const idMapFile& map, const char* key, const char* value )
{
	for( int i = 0; i < map.GetNumEntities(); ++i )
	{
		const idDict& args = map.GetEntity( i )->epairs;
		if( idStr::Icmp( args.GetString( key ), value ) == 0 )
		{
			idVec3 origin;
			if( args.GetVector( "origin", "0 0 0", origin ) )
			{
				return origin;
			}
			break;
		}
	}
	Sys_Error( "Relay Station requires %s %s with an origin in %s", key, value, RELAY_MAP );
	return vec3_zero;
}

class RelayStation
{
public:
	explicit RelayStation( const idMapFile& map );
	~RelayStation();
	void Reset();
	void Look( float yawDelta, float pitchDelta );
	void Interact();
	void Step( const std::array<bool, K_LAST_KEY>& keys, bool jumpPressed, int now );
	void Draw( int now, float seconds );
	void Capture() const;

private:
	int AddModel( const char* name );
	void MoveModel( int handle, const idVec3& translation );
	void MoveDrone();
	void DrawHud( float seconds ) const;
	int WalkArea( const idVec3& position ) const;

	idRenderWorld* world;
	idEntity playerOwner;
	idEntity gateOwner;
	std::unique_ptr<idPhysics_Player> player;
	std::unique_ptr<idAAS> aas;
	idClipModel droneHull;
	const idVec3 spawn;
	const idVec3 gateOrigin;
	const idVec3 cellOrigin;
	const idVec3 droneSpawn;
	const idVec3 droneGoal;
	const idVec3 exitOrigin;
	int gate;
	int cell;
	int drone;
	int droneGoalArea;
	int portal;
	int frameWidth = 0;
	int frameHeight = 0;
	idVec3 dronePosition;
	float yaw = 0;
	float pitch = 0;
	bool carrying = false;
	bool gateOpen = false;
	bool droneArrived = false;
	bool won = false;
	bool jumpLogged = false;
	bool stepLogged = false;
	bool crouchLogged = false;
	bool ladderLogged = false;
	bool gateBlockedLogged = false;
};

RelayStation::RelayStation( const idMapFile& map ) :
	world( renderSystem->AllocRenderWorld() ),
	spawn( RelayOrigin( map, "classname", "info_player_start" ) ),
	gateOrigin( RelayOrigin( map, "name", "relay_gate" ) ),
	cellOrigin( RelayOrigin( map, "name", "relay_cell" ) ),
	droneSpawn( RelayOrigin( map, "name", "relay_drone" ) ),
	droneGoal( RelayOrigin( map, "classname", "relay_drone_goal" ) ),
	exitOrigin( RelayOrigin( map, "classname", "relay_exit" ) )
{
	if( !world->InitFromMap( RELAY_MAP ) )
	{
		Sys_Error( "Could not load the compiled Relay Station render world" );
	}
	collisionModelManager->LoadMap( &map, false );
	gameLocal.clip.Init();
	gateOwner.name = "relay_gate";
	gateOwner.entityNumber = MAX_CLIENTS;
	gateOwner.SetPhysics( nullptr );
	gateOwner.GetPhysics()->SetSelf( &gateOwner );
	idClipModel* gateHull = new idClipModel;
	if( !gateHull->LoadModel( "relay_gate" ) )
	{
		delete gateHull;
		Sys_Error( "Relay Station gate collision model is missing" );
	}
	gateOwner.GetPhysics()->SetClipModel( gateHull, 1 );
	droneHull.LoadModel( idTraceModel( idBounds( idVec3( -10, -10, 0 ), idVec3( 10, 10, 19 ) ) ) );

	gate = AddModel( "relay_gate" );
	cell = AddModel( "relay_cell" );
	drone = AddModel( "relay_drone" );
	AddModel( "relay_beacon" );
	portal = world->FindPortal( gateHull->GetBounds().Expand( 1 ) );
	if( !portal )
	{
		Sys_Error( "Relay Station gate needs a compiled render portal" );
	}
	aas.reset( idAAS::Alloc() );
	if( !aas->Init( idStr( RELAY_MAP ) + ".aas48", map.GetGeometryCRC() ) )
	{
		Sys_Error( "Could not load Relay Station navigation" );
	}
	droneGoalArea = WalkArea( droneGoal );
	const int droneStartArea = WalkArea( droneSpawn );
	aasPath_t path;
	if( !droneStartArea || !droneGoalArea || droneStartArea == droneGoalArea ||
		!aas->WalkPathToGoal( path, droneStartArea, droneSpawn, droneGoalArea, droneGoal, WALK_FLAGS ) )
	{
		Sys_Error( "Relay Station drone needs a walk route between distinct areas (%d -> %d)", droneStartArea, droneGoalArea );
	}
	common->Printf( "Relay: AAS route %d -> %d\n", droneStartArea, droneGoalArea );

	cvarSystem->SetCVarFloat( "pm_normalheight", STAND_HEIGHT );
	cvarSystem->SetCVarFloat( "pm_crouchheight", CROUCH_HEIGHT );
	cvarSystem->SetCVarBool( "pm_usecylinder", false );
	Reset();
	globalImages->LoadDeferredImages();
}

RelayStation::~RelayStation()
{
	player.reset();
	gateOwner.GetPhysics()->SetClipModel( nullptr, 1 );
	gameLocal.clip.Shutdown();
	collisionModelManager->FreeMap();
	renderSystem->FreeRenderWorld( world );
}

int RelayStation::AddModel( const char* name )
{
	renderEntity_t entity = {};
	entity.hModel = renderModelManager->FindModel( name );
	if( !entity.hModel || entity.hModel->IsDefaultModel() )
	{
		Sys_Error( "Relay Station render model is missing: %s", name );
	}
	entity.axis = mat3_identity;
	entity.shaderParms[0] = entity.shaderParms[1] = entity.shaderParms[2] = entity.shaderParms[3] = 1;
	return world->AddEntityDef( &entity );
}

void RelayStation::MoveModel( int handle, const idVec3& translation )
{
	renderEntity_t entity = *world->GetRenderEntity( handle );
	entity.origin = translation;
	world->UpdateEntityDef( handle, &entity );
}

void RelayStation::Reset()
{
	player.reset( new idPhysics_Player );
	playerOwner.RestorePhysics( player.get() );
	player->SetSelf( &playerOwner );
	player->SetGravity( idVec3( 0, 0, -1050 ) );
	player->SetSpeed( 175, 105 );
	player->SetMaxStepHeight( 18 );
	player->SetMaxJumpHeight( 42 );
	player->SetClipMask( MASK_PLAYERSOLID );
	player->SetClipModel( new idClipModel( idTraceModel( idBounds(
		idVec3( -PLAYER_RADIUS, -PLAYER_RADIUS, 0 ), idVec3( PLAYER_RADIUS, PLAYER_RADIUS, STAND_HEIGHT ) ) ) ), 1 );
	player->SetContents( CONTENTS_BODY );
	player->SetOrigin( spawn );

	gateOwner.GetPhysics()->GetClipModel()->Link( gameLocal.clip, &gateOwner, 0, vec3_zero, mat3_identity );
	world->SetPortalState( portal, PS_BLOCK_VIEW );
	MoveModel( gate, vec3_zero );
	MoveModel( cell, vec3_zero );
	MoveModel( drone, vec3_zero );
	dronePosition = droneSpawn;
	yaw = pitch = 0;
	carrying = gateOpen = droneArrived = won = false;
	jumpLogged = stepLogged = crouchLogged = ladderLogged = gateBlockedLogged = false;
	common->Printf( "Relay: reset\n" );
}

void RelayStation::Look( float yawDelta, float pitchDelta )
{
	yaw = idMath::AngleNormalize180( yaw + yawDelta );
	pitch = idMath::ClampFloat( -80, 80, pitch + pitchDelta );
}

void RelayStation::Interact()
{
	const idVec3 position = player->GetOrigin();
	if( won || gateOpen || ( gateOrigin.ToVec2() - position.ToVec2() ).LengthSqr() > Square( 64.0f ) )
	{
		return;
	}
	if( !carrying )
	{
		return;
	}
	gateOpen = true;
	gateOwner.GetPhysics()->GetClipModel()->Unlink();
	MoveModel( gate, idVec3( 0, 0, 96 ) );
	world->SetPortalState( portal, PS_BLOCK_NONE );
	common->Printf( "Relay: gate opened\n" );
}

int RelayStation::WalkArea( const idVec3& position ) const
{
	return aas->PointReachableAreaNum( position, idBounds( idVec3( -12, -12, -16 ), idVec3( 12, 12, 16 ) ), AREA_REACHABLE_WALK );
}

void RelayStation::MoveDrone()
{
	const int area = WalkArea( dronePosition );
	aasPath_t path;
	if( !area || !aas->WalkPathToGoal( path, area, dronePosition, droneGoalArea, droneGoal, WALK_FLAGS ) )
	{
		return;
	}

	idVec3 delta = path.moveGoal - dronePosition;
	delta.z = 0;
	const float distance = delta.Normalize();
	const idVec3 end = dronePosition + delta * Min( distance, 90.0f * TICK_MS * 0.001f );
	trace_t trace;
	gameLocal.clip.Translation( trace, dronePosition, end, &droneHull, mat3_identity, CONTENTS_SOLID, nullptr );
	dronePosition = trace.endpos;
	MoveModel( drone, dronePosition - droneSpawn );
	if( ( dronePosition - droneGoal ).LengthSqr() < Square( 5.0f ) )
	{
		droneArrived = true;
		common->Printf( "Relay: drone arrived\n" );
	}
}

void RelayStation::Step( const std::array<bool, K_LAST_KEY>& keys, bool jumpPressed, int now )
{
	if( won )
	{
		return;
	}
	Look( 1.8f * ( int( keys[K_LEFTARROW] ) - int( keys[K_RIGHTARROW] ) ),
		  1.4f * ( int( keys[K_DOWNARROW] ) - int( keys[K_UPARROW] ) ) );
	usercmd_t command = {};
	command.forwardmove = 127 * ( int( keys[K_W] ) - int( keys[K_S] ) );
	command.rightmove = 127 * ( int( keys[K_D] ) - int( keys[K_A] ) );
	command.buttons = ( keys[K_SPACE] || jumpPressed ? BUTTON_JUMP : 0 ) | ( keys[K_C] ? BUTTON_CROUCH : 0 );
	player->SetPlayerInput( command, idAngles( pitch, yaw, 0 ).ToForward() );
	player->Evaluate( TICK_MS, now );

	if( !jumpLogged && player->HasJumped() )
	{
		common->Printf( "Relay: jumped\n" );
		jumpLogged = true;
	}
	if( !stepLogged && player->HasSteppedUp() )
	{
		common->Printf( "Relay: stepped up\n" );
		stepLogged = true;
	}
	if( !crouchLogged && player->IsCrouching() )
	{
		common->Printf( "Relay: crouched\n" );
		crouchLogged = true;
	}
	if( !ladderLogged && player->OnLadder() )
	{
		common->Printf( "Relay: ladder engaged\n" );
		ladderLogged = true;
	}

	const idVec3 position = player->GetOrigin();
	if( !carrying && ( position - cellOrigin ).LengthSqr() < Square( 30.0f ) )
	{
		carrying = true;
		MoveModel( cell, idVec3( 0, 0, -128 ) );
		common->Printf( "Relay: power cell collected\n" );
	}
	if( !gateOpen && !gateBlockedLogged && command.forwardmove > 0 &&
		( position.ToVec2() - gateOrigin.ToVec2() ).LengthSqr() < Square( 26.0f ) &&
		player->GetLinearVelocity().ToVec2().LengthSqr() < 1 )
	{
		gateBlockedLogged = true;
		common->Printf( "Relay: closed gate blocked movement\n" );
	}
	if( gateOpen && !droneArrived )
	{
		MoveDrone();
	}
	if( droneArrived && ( position - exitOrigin ).LengthSqr() < Square( 28.0f ) )
	{
		won = true;
		common->Printf( "Relay: level complete\n" );
	}
}

void RelayStation::DrawHud( float seconds ) const
{
	ImGuiIO& io = ImGui::GetIO();
	io.IniFilename = nullptr;
	io.DisplaySize = ImVec2( frameWidth, frameHeight );
	io.DeltaTime = idMath::ClampFloat( 0.001f, 0.05f, seconds );
	ImGui::NewFrame();
	ImDrawList* hud = ImGui::GetForegroundDrawList();
	const ImU32 panel = IM_COL32( 12, 22, 31, 235 );
	const ImU32 white = IM_COL32( 225, 239, 242, 255 );
	const ImU32 accent = IM_COL32( 89, 240, 193, 255 );

	const char* objective = "Crouch under the duct and collect the power cell.";
	if( carrying )
	{
		objective = "Press E at the gate to install the power cell.";
	}
	if( gateOpen )
	{
		objective = "Follow the drone. Hold W at the gold ladder.";
	}
	if( droneArrived )
	{
		objective = "Climb the ladder and reach the gold transmitter.";
	}
	hud->AddRectFilled( ImVec2( 12, 12 ), ImVec2( 458, 68 ), panel, 5 );
	hud->AddText( ImVec2( 24, 21 ), accent, "RELAY STATION" );
	hud->AddText( ImVec2( 24, 44 ), white, objective );
	const char* controls = "WASD Move  Mouse Look  Space Jump  C Crouch  E Use  R Restart  Esc Exit";
	hud->AddRectFilled( ImVec2( 12, frameHeight - 38 ),
						ImVec2( 36 + ImGui::CalcTextSize( controls ).x, frameHeight - 12 ), panel, 5 );
	hud->AddText( ImVec2( 24, frameHeight - 32 ), white, controls );

	const ImVec2 center( frameWidth * 0.5f, frameHeight * 0.5f );
	hud->AddCircle( center, 3, white, 12 );
	if( won )
	{
		hud->AddRectFilled( ImVec2( center.x - 122, center.y - 38 ), ImVec2( center.x + 122, center.y + 38 ), panel, 5 );
		hud->AddText( ImVec2( center.x - 58, center.y - 21 ), accent, "RELAY ONLINE" );
		hud->AddText( ImVec2( center.x - 64, center.y + 4 ), white, "R Restart   Esc Exit" );
	}
	ImGui::Render();
	renderSystem->SetGLState( GLS_DEPTHFUNC_ALWAYS | GLS_SRCBLEND_SRC_ALPHA | GLS_DSTBLEND_ONE_MINUS_SRC_ALPHA );
	backEnd.ImGui_RenderDrawLists( ImGui::GetDrawData() );
}

void RelayStation::Capture() const
{
	common->Printf( "Relay: capture at %s, view %.1f %.1f\n", player->GetOrigin().ToString( 1 ), yaw, pitch );
	renderSystem->SwapCommandBuffers( nullptr, nullptr, nullptr, nullptr, nullptr, nullptr );
	if( !R_WriteRendererEvidence( "screenshots/relay-station.png" ) )
	{
		common->Warning( "Could not capture the Relay Station frame" );
	}
}

void RelayStation::Draw( int now, float seconds )
{
	const int width = renderSystem->GetWidth();
	const int height = renderSystem->GetHeight();
	if( width <= 0 || height <= 0 )
	{
		return;
	}
	if( width != frameWidth || height != frameHeight )
	{
		renderSystem->SwapCommandBuffers( nullptr, nullptr, nullptr, nullptr, nullptr, nullptr );
		frameWidth = width;
		frameHeight = height;
	}

	renderView_t view = {};
	view.viewID = 1;
	view.vieworg = player->GetOrigin() + idVec3( 0, 0, player->IsCrouching() ? 31 : 56 );
	view.vieworg_weapon = view.vieworg;
	view.viewaxis = idAngles( pitch, yaw, 0 ).ToMat3();
	view.fov_x = 90;
	view.fov_y = 2.0f * RAD2DEG( idMath::ATan( float( height ) / width ) );
	view.time[0] = view.time[1] = now;
	view.rdflags = RDF_NOSHADOWS | RDF_NOAMBIENT;
	world->RenderScene( &view );
	DrawHud( seconds );
	const emptyCommand_t* commands = renderSystem->SwapCommandBuffers( nullptr, nullptr, nullptr, nullptr, nullptr, nullptr );
	renderSystem->RenderCommandBuffers( commands );
}

void RunRelayLoop( RelayStation& station )
{
	relayQuitRequested = false;
	cmdSystem->RemoveCommand( "quit" );
	cmdSystem->AddCommand( "quit", RelayQuit_f, CMD_FL_SYSTEM, "exit Relay Station" );
	Sys_GrabMouseCursor( true );

	std::array<bool, K_LAST_KEY> keys = {};
	int previous = Sys_Milliseconds();
	int available = 0;
	bool jumpPressed = false;
	station.Draw( previous, 0.016f );
	common->Printf( "Relay: ready\n" );
	while( !relayQuitRequested )
	{
		Sys_GenerateEvents();
#ifdef _WIN32
		int mouseEvents[MAX_MOUSE_EVENTS][2];
		Sys_PollMouseInputEvents( mouseEvents );
#endif
		for( sysEvent_t event = Sys_GetEvent(); event.evType != SE_NONE; event = Sys_GetEvent() )
		{
			if( event.IsKeyEvent() && event.evValue > K_NONE && event.evValue < K_LAST_KEY )
			{
				if( event.IsKeyDown() && !keys[event.evValue] )
				{
					switch( event.GetKey() )
					{
						case K_ESCAPE: relayQuitRequested = true; break;
						case K_E: station.Interact(); break;
						case K_R: station.Reset(); break;
						case K_SPACE: jumpPressed = true; break;
						case K_F12:
							station.Capture();
							break;
						default: break;
					}
				}
				keys[event.evValue] = event.IsKeyDown();
			}
			if( event.evType == SE_MOUSE )
			{
				station.Look( -0.12f * event.evValue, 0.12f * event.evValue2 );
			}
			if( event.evPtr )
			{
				if( event.evType == SE_CONSOLE && idStr::Cmp( static_cast<const char*>( event.evPtr ), "quit" ) == 0 )
				{
					relayQuitRequested = true;
				}
				Mem_Free( event.evPtr );
			}
		}
		cmdSystem->ExecuteCommandBuffer();
		if( relayQuitRequested )
		{
			break;
		}
		if( !cvarSystem->GetCVarBool( "com_activeApp" ) )
		{
			keys.fill( false );
			jumpPressed = false;
		}

		const int now = Sys_Milliseconds();
		const int elapsed = idMath::ClampInt( 0, 100, now - previous );
		previous = now;
		available += elapsed;
		while( available >= TICK_MS )
		{
			available -= TICK_MS;
			station.Step( keys, jumpPressed, now - available );
			jumpPressed = false;
		}
		station.Draw( now, elapsed * 0.001f );
		Sys_Sleep( 8 );
	}
	Sys_GrabMouseCursor( false );
}
}

void RunNativeRelay()
{
	idMapFile map;
	if( !map.Parse( RELAY_MAP, true ) )
	{
		Sys_Error( "Could not read the Relay Station map. Start the engine with the Relay Station launcher." );
	}
	// Physics owners use game entity type checks during collision and destruction.
	idEvent::Init();
	idClass::Init();
	{
		RelayStation station( map );
		RunRelayLoop( station );
	}
	idClass::Shutdown();
	idEvent::Shutdown();
}
