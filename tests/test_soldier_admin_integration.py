from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUD = ROOT / "source" / "upstream" / "mudlib"


def read(path):
    return (MUD / path).read_text(encoding="utf-8")


def test_soldier_skill_daemons_register_canonical_ids():
    expected = {
        "daemon/skill/berserk.c": "berserk",
        "daemon/skill/powerblow.c": "powerblow",
        "daemon/skill/heavy_parry.c": "heavy_parry",
    }
    for path, skill in expected.items():
        s = read(path)
        assert 'DAEMON_D->register_skill_daemon("%s");' % skill in s
        assert 'seteuid(getuid());' in s
        assert 'string type()' in s
        assert 'return "martial";' in s


def test_recruit_stone_grants_initial_soldier_skills_only_to_commoner():
    s = read("custom/zhenwu/obj/recruit_stone.c")
    for skill in ("berserk", "powerblow"):
        assert 'me->set_skill("%s", 1);' % skill in s
        assert 'me->set_learn("%s", 1);' % skill in s
    # Heavy parry is taught later by Mee Pei after level and merit requirements.
    assert 'me->set_skill("heavy_parry", 1);' not in s
    assert 'me->set_learn("heavy_parry", 1);' not in s
    mee_pei = read("custom/zhenwu/npc/mee_pei.c")
    assert '#define HEAVY_PARRY_MERIT 100000' in mee_pei
    assert 'me->improve_skill_exact("heavy_parry", 1);' in mee_pei
    assert 'if( origin_class == "commoner" )' in s
    assert 'me->set_class("soldier");' in s
    # A fighter enlistment changes class but must not silently receive the
    # three signature soldier skills.
    assert 'origin_class != "commoner" && origin_class != "fighter"' in s


def test_berserk_requires_learning_combat_and_two_handed_weapon():
    s = read("cmds/std/berserk.c")
    assert 'me->query_learn("berserk", 1)' in s
    assert 'me->is_fighting()' in s
    assert 'skill[0..8] != "twohanded"' in s
    assert 'me->start_busy(2);' in s
    assert 'kee_cost = me->query_stat_maximum("kee") / 8;' in s
    assert 'me->consume_stat("kee", kee_cost);' in s


def test_powerblow_is_applied_in_low_level_combat():
    s = read("adm/daemons/combatd.c")
    assert 'me->query_learn("powerblow")' in s
    assert 'me->query_skill("powerblow") > 0' in s
    assert 'strength += strength * me->query_skill("powerblow") / 800;' in s
    # At skill 200 the multiplier is exactly +25%.
    assert 200 // 800 == 0
    assert 200 * 100 // 800 == 25


def test_heavy_parry_is_a_registered_skill_and_has_two_multiplier_paths():
    daemon = read("daemon/skill/heavy_parry.c")
    combat = read("feature/char/combat.c")
    assert 'DAEMON_D->register_skill_daemon("heavy_parry");' in daemon
    assert 'return "martial";' in daemon
    assert 'query_learn("heavy_parry")' in combat
    assert 'max *= (objectp(attacker) && attacker->query_skill("force") > 0) ? 5 : 2;' in combat


def test_admin_skill_commands_are_part_of_same_contract():
    s = read("cmds/adm/admin.c")
    for command in (
        'admin skill <技能名稱> <等級> [玩家]',
        'admin learn <技能名稱> [玩家]',
        'admin unlearn <技能名稱> [玩家]',
        'admin enable <技能名稱> [玩家]',
    ):
        assert command in s
    assert 'replace_string(name, " ", "_")' in s
    assert 'return name;' in s
    assert 'ob->set_learn(resolved, 0);' in s
    assert 'ob->set_skill(resolved, 0);' in s


def test_player_sync_covers_admin_relevant_character_files():
    s = (ROOT / "server" / "player-sync.js").read_text(encoding="utf-8")
    assert "const AREAS=['user','login','mail'];" in s
    assert "es2_player_files" in s
