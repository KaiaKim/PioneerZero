import asyncio
from ...util import conM, dbM
from ...services.game_core import join
from . import timer

### phase flow functions
async def handle_phase(game):
    phase_task = getattr(game, "phase_task", None)
    if phase_task and not phase_task.done():
        return
    game.phase_task = asyncio.create_task(_phase_flow(game))

async def _phase_flow(game):
    try:
        await timer.offset_timer(game)
        if not await kickoff(game):
            return

        game.in_combat = True
        await timer.offset_timer(game)
        await position_declaration(game)
        await timer.phase_timer(game)
        await position_resolution(game)
        
        defeated_team = None
        for _ in range(game.max_rounds):
            await timer.offset_timer(game)
            await start_round(game)
            await timer.offset_timer(game)
            await action_declaration(game)
            await timer.phase_timer(game)

            await timer.offset_timer(game)
            await action_resolution(game)

            defeated_team = await end_round(game)
            if defeated_team is not None:
                break

        if defeated_team is None:
            defeated_team = game.check_all_players_defeated()[1]

        await timer.offset_timer(game)
        await wrap_up(game, defeated_team)
        game.in_combat = False

    except asyncio.CancelledError:
        pass
    except Exception as exc:
        print(f"Phase flow error: {exc}")
    finally:
        if getattr(game, "phase_task", None) is asyncio.current_task():
            game.phase_task = None

async def kickoff(game):
    if not join.are_all_players_ready(game):
        return False

    # Save initial combat snapshot (one-time backup)
    dbM.save_game_session(game)
    
    result = f"전투 {game.id}를 시작합니다."
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)
    
    await conM.broadcast_to_game(game.id, {
        "type": "combat_started"
    })
    return True
    
async def position_declaration(game):
    game.phase = 'position_declaration'
    result = '위치 선언 페이즈입니다. 시작 위치를 선언해주세요.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def position_resolution(game):
    game.auto_fill_action()
    results = game.resolve_actions()

    for result in results:
        msg = dbM.save_chat(game.id, result)
        await conM.broadcast_to_game(game.id, msg)
        await asyncio.sleep(1)
    
    final_pos_list = [f"{player.character.name}: {player.pos}" for player in game.player_slots]
    result = "위치 선언이 종료되었습니다. 시작 위치는 다음과 같습니다: \n" + "\n".join(final_pos_list)
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def start_round(game):
    game.current_round += 1
    result = f'라운드 {game.current_round} 선언 페이즈입니다.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def action_declaration(game):
    game.phase = 'action_declaration'
    game.action_queue = []
    result = f'스킬과 행동을 선언해주세요.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)
    await conM.broadcast_to_game(game.id, {
        "type": "action_submission_update",
        "submitted": game.get_action_submission_status()
    })

async def action_resolution(game):
    game.phase = 'resolution'
    result = f'라운드 {game.current_round} 해결 페이즈입니다. 계산을 시작합니다.'
    msg = dbM.save_chat(game.id, result)
    await conM.broadcast_to_game(game.id, msg)

async def end_round(game):
    """라운드 종료 방송"""
    is_team_defeated, defeated_team = game.check_all_players_defeated()
    
    if is_team_defeated:
        return defeated_team

    return None

async def wrap_up(game, defeated_team: int):
    """전투 종료 단계 처리"""
    game.phase = 'wrap-up'
    game.in_combat = False
    winner = 'white' if defeated_team == 0 else 'blue'
    return '전투가 종료되었습니다. {} 팀이 승리했습니다.'.format(winner)
