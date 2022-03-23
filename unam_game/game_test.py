import pytest
import yaml
import pathlib
import random
import time
from typing import Tuple

import engine.controllers.turn as _turn
import engine.controllers.context as _context
import engine.controllers.game as _game

from engine.models.rules import ScriptModel, EngineConfigModel
from engine.controllers.rules import RuleSet, rules_manager
from engine.models import AttributeModel, AttributeGroupModel, CharacterModel, CharacterSheetModel, \
    CharacterValueModel, ValueDefinitionModel, StringValueModel, IntegerValueModel
from engine.controllers.characters import character_manager, set_random_character_number_values


turn_manager = _turn.turn_manager
TurnsManager = _turn.TurnsManager
Context = _context.Context


async def create_character_sheet():

    attrs = await AttributeModel.objects.all()
    attrs_grps = await AttributeGroupModel.objects.all()
    chars = await CharacterModel.objects.all()
    sheets = await CharacterSheetModel.objects.all()
    vals = await CharacterValueModel.objects.all()
    vals_defs = await ValueDefinitionModel.objects.all()
    str_vals = await StringValueModel.objects.all()
    int_vals = await IntegerValueModel.objects.all()

    for definition_list in [attrs, attrs_grps, chars, sheets, vals, vals_defs, str_vals, int_vals]:
        for definition in definition_list:
            await definition.delete()


    character_base_sheet_rs= yaml.safe_load(
        open(pathlib.Path('engine/tests/unam_game//ruleset/characters/base_sheets.yaml'))
    )

    rule_set = RuleSet(**character_base_sheet_rs)

    await rules_manager.create_rule_definition(rule_set)

    await character_manager.load_characters_sheets()

    return await CharacterSheetModel.objects.get(name=rule_set.character_sheets[0].name)


@pytest.fixture
async def character_sheet():
    return await create_character_sheet()


@pytest.fixture
async def turn_manager_instance_setup():

    scripts = await ScriptModel.objects.all()
    for script in scripts:
        await script.delete()

    configs = await EngineConfigModel.objects.all()
    for conf in configs:
        await conf.delete()

    turns_config_rs = yaml.safe_load(
        open(pathlib.Path('engine/tests/unam_game/ruleset/turns/turns_config.yaml'))
    )
    turn_scripts_rs = yaml.safe_load(
        open(pathlib.Path('engine/tests/unam_game/ruleset/turns/scripts.yaml'))
    )
    combat_scripts_rs = yaml.safe_load(
        open(pathlib.Path('engine/tests/unam_game//ruleset/combat/scripts.yaml'))
    )

    for rule_set in [turns_config_rs, turn_scripts_rs, combat_scripts_rs]:
        rule_set_schema = RuleSet(**rule_set)
        await rules_manager.create_rule_definition(rule_set_schema)


@pytest.fixture
async def test_characters(character_sheet):
    print("\n TEST TURN WITH 2 CHARACTERS \n")
    char_1 = await character_manager.create_character(name="Character 1",
                                                      character_sheets_id_list=[character_sheet.id])
    char_2 = await character_manager.create_character(name="Character 2",
                                                      character_sheets_id_list=[character_sheet.id])

    await set_random_character_number_values(char_1["id"], 10, 15)
    await set_random_character_number_values(char_2["id"], 10, 15)

    char_1 = await character_manager.get_character(char_1["id"])
    char_2 = await character_manager.get_character(char_2["id"])

    return char_1, char_2


@pytest.mark.asyncio
async def test_game_setup_and_combat_mode(test_characters: Tuple,
                                          turn_manager_instance_setup):
    char_1, char_2 = test_characters
    await _game.game_manager.setup_game([char_1["id"], char_2["id"]])
    await _game.game_manager.start_game()
