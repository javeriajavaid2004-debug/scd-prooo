"""Scrolling level manager with hazards, attempt tracking, and Community Troll logic."""

from __future__ import annotations

import math
from typing import List, Optional, Dict, Any, Tuple

import pygame

import config
from database_manager import db_manager
import random
import math
# IMPORTANT: DisappearingPlatform must be imported here
from hazards import OscillatingHazard, TriggerSpike, SwingingAxe, ChasingHazard, DisappearingPlatform, CrushingHazard 

TILE = config.TILE_SIZE
GROUND_Y = config.SCREEN_HEIGHT - TILE
LEVEL_LENGTH = config.SCREEN_WIDTH * config.LEVEL_SCROLL_LENGTH

def R(x, y, w, h) -> Tuple[int, int, int, int]:
    return (TILE * x, GROUND_Y - TILE * y, TILE * w, TILE * h)


# --- LEVEL BLUEPRINTS (12 LEVELS + 1 BOSS) ---

LEVEL_BLUEPRINTS: List[Dict[str, Any]] = [
    # --- Level 1: The Descent (Enhanced) ---
    {
        "id": 1, "name": "Level 1: The Descent",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(75, 2, 2, 3), 
        "platforms": [
            R(0, 1, 10, 1), 
            R(12, 3, 3, 1), R(18, 5, 3, 1), R(24, 7, 5, 1), 
            R(35, 4, 5, 1), R(45, 2, 10, 1), R(60, 1, 15, 1)
        ],
        "static_traps": [R(10, 1, 2, 1), R(30, 1, 5, 1), R(55, 1, 5, 1)],
        "oscillators": [
            {"rect": R(40, 6, 2, 1), "axis": "y", "amplitude": 100, "speed": 3.0},
            {"rect": R(15, 5, 2, 1), "axis": "x", "amplitude": 60, "speed": 2.5}
        ],
        "triggers": [
            {"trigger": R(24, 8, 2, 2), "spike": R(26, 7, 1, 1)}, 
            {"trigger": R(68, 2, 2, 2), "spike": R(70, 1, 1, 1)}, 
        ],
        "axes": [
            {"pivot": R(30, 10, 1, 1)[0:2], "length": 120, "swing_degrees": 60, "speed": 1.5},
            {"pivot": R(50, 8, 1, 1)[0:2], "length": 100, "swing_degrees": 45, "speed": 2.0}
        ],
        "chasers": [
            {"spawn": R(45, 8, 1, 1)[0:2], "speed": 100.0, "max_time": 3.0},
            {"spawn": R(65, 5, 1, 1)[0:2], "speed": 120.0, "max_time": 4.0}
        ],
        "disappear": [
            {"trigger": R(35, 5, 2, 2), "platform": R(35, 4, 5, 1)}
        ],
        "crushers": [
            {"rect": R(50, 12, 2, 2), "slam_height": 380},
            {"rect": R(10, 10, 2, 2), "slam_height": 300}
        ]
    },
    # --- Level 2: Moving Ground (Enhanced) ---
    {
        "id": 2, "name": "Level 2: The Grinder",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(85, 8, 2, 3), 
        "platforms": [
            R(0, 1, 10, 1), 
            R(15, 3, 5, 1), 
            R(25, 5, 4, 1), 
            R(35, 7, 4, 1),
            R(45, 1, 15, 1),
            R(65, 4, 5, 1),
            R(75, 6, 12, 1)
        ],
        "static_traps": [R(10, 1, 35, 1), R(60, 1, 15, 1)],
        "oscillators": [
            {"rect": R(20, 4, 2, 1), "axis": "y", "amplitude": 80, "speed": 4.0},
            {"rect": R(40, 6, 2, 1), "axis": "x", "amplitude": 120, "speed": 2.5}, 
        ],
        "triggers": [
            {"trigger": R(45, 2, 5, 2), "spike": R(47, 2, 1, 1)},
            {"trigger": R(75, 7, 3, 2), "spike": R(78, 6, 1, 1)},
        ],
        "axes": [
            {"pivot": R(55, 10, 1, 1)[0:2], "length": 150, "swing_degrees": 90, "speed": 2.0},
            {"pivot": R(35, 12, 1, 1)[0:2], "length": 120, "swing_degrees": 60, "speed": 2.5},
        ],
        "chasers": [
            {"spawn": R(70, 7, 1, 1)[0:2], "speed": 180.0, "max_time": 3.0},
            {"spawn": R(10, 6, 1, 1)[0:2], "speed": 150.0, "max_time": 5.0}
        ],
        "disappear": [
            {"trigger": R(25, 6, 2, 2), "platform": R(25, 5, 4, 1)}
        ],
        "crushers": [
            {"rect": R(30, 12, 3, 2), "slam_height": 380},
            {"rect": R(50, 12, 2, 2), "slam_height": 400},
            {"rect": R(80, 10, 2, 2), "slam_height": 200}
        ]
    },
    # --- Level 3: Smooth Sailing (Enhanced) ---
    {
        "id": 3, "name": "Level 3: Trust Issues",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(100, 1, 3, 3), 
        "platforms": [
            R(0, 1, 15, 1), 
            R(20, 3, 10, 1), 
            R(40, 5, 10, 1),
            R(60, 3, 10, 1),
            R(80, 1, 20, 1)
        ],
        "static_traps": [R(15, 1, 5, 1), R(30, 1, 10, 1), R(50, 1, 10, 1), R(70, 1, 10, 1)],
        "oscillators": [
            {"rect": R(25, 6, 2, 1), "axis": "y", "amplitude": 120, "speed": 3.5},
            {"rect": R(55, 4, 2, 1), "axis": "x", "amplitude": 80, "speed": 2.2}
        ],
        "triggers": [
            {"trigger": R(40, 6, 3, 2), "spike": R(43, 5, 1, 1)},
            {"trigger": R(85, 2, 3, 2), "spike": R(88, 1, 1, 1)},
            {"trigger": R(10, 3, 2, 2), "spike": R(12, 1, 1, 1)}
        ],
        "axes": [
            {"pivot": R(50, 10, 1, 1)[0:2], "length": 140, "swing_degrees": 80, "speed": 2.0},
            {"pivot": R(75, 12, 1, 1)[0:2], "length": 120, "swing_degrees": 60, "speed": 2.5}
        ],
        "chasers": [
            {"spawn": R(20, 10, 1, 1)[0:2], "speed": 120.0, "max_time": 3.0},
            {"spawn": R(90, 5, 1, 1)[0:2], "speed": 150.0, "max_time": 4.0}
        ],
        "disappear": [
            {"trigger": R(40, 0, 10, 10), "platform": R(40, 5, 10, 1)},
            {"trigger": R(60, 0, 10, 10), "platform": R(60, 3, 10, 1)}
        ],
        "crushers": [
            {"rect": R(10, 12, 2, 2), "slam_height": 400}
        ]
    },
    # --- Level 4: The Gauntlet (Enhanced) ---
    {
        "id": 4, "name": "Level 4: The Gauntlet",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(130, 2, 2, 3), 
        "platforms": [
            R(0, 1, 10, 1), 
            R(25, 7, 6, 1),
            R(50, 6, 35, 1),
            R(95, 3, 12, 1),
            R(115, 1, 20, 1)
        ],
        "static_traps": [R(10, 1, 5, 1), R(41, 1, 9, 1), R(85, 6, 10, 1), R(107, 3, 8, 1)],
        "oscillators": [
            {"rect": R(20, 8, 2, 1), "axis": "y", "amplitude": 60, "speed": 5.0},
            {"rect": R(70, 10, 2, 1), "axis": "y", "amplitude": 80, "speed": 4.0},
            {"rect": R(105, 5, 2, 1), "axis": "x", "amplitude": 100, "speed": 3.0}
        ],
        "triggers": [
            {"trigger": R(50, 7, 2, 2), "spike": R(52, 6, 1, 1)},
            {"trigger": R(65, 7, 2, 2), "spike": R(67, 6, 1, 1)},
            {"trigger": R(80, 7, 2, 2), "spike": R(82, 6, 1, 1)},
            {"trigger": R(110, 2, 2, 2), "spike": R(112, 1, 1, 1)},
        ],
        "axes": [
            {"pivot": R(45, 13, 1, 1)[0:2], "length": 160, "swing_degrees": 80, "speed": 2.5},
            {"pivot": R(90, 11, 1, 1)[0:2], "length": 140, "swing_degrees": 60, "speed": 3.0},
            {"pivot": R(120, 10, 1, 1)[0:2], "length": 120, "swing_degrees": 90, "speed": 3.5},
        ],
        "chasers": [
            {"spawn": R(55, 12, 1, 1)[0:2], "speed": 220.0, "max_time": 4.0},
            {"spawn": R(100, 6, 1, 1)[0:2], "speed": 240.0, "max_time": 3.0},
            {"spawn": R(20, 5, 1, 1)[0:2], "speed": 200.0, "max_time": 4.0},
            {"spawn": R(125, 8, 1, 1)[0:2], "speed": 260.0, "max_time": 5.0}
        ],
        "disappear": [
            {"trigger": R(12, 4, 3, 2), "platform": R(15, 4, 6, 1)},
            {"trigger": R(32, 9, 3, 2), "platform": R(35, 9, 6, 1)}
        ],
        "crushers": [
            {"rect": R(60, 16, 2, 2), "slam_height": 550},
            {"rect": R(75, 16, 2, 2), "slam_height": 550},
            {"rect": R(95, 14, 2, 2), "slam_height": 400},
        ]
    },
    # --- Level 5: Crushing Depths (Enhanced) ---
    {
        "id": 5, "name": "Level 5: Crushing Depths",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(110, 1, 3, 5), 
        "platforms": [
            R(0, 1, 10, 1), 
            R(15, 3, 8, 1), 
            R(28, 6, 8, 1), 
            R(42, 9, 8, 1),
            R(55, 6, 8, 1), 
            R(70, 3, 8, 1), 
            R(85, 1, 30, 1)
        ],
        "static_traps": [R(10, 1, 5, 1), R(23, 1, 5, 1), R(36, 1, 6, 1), R(50, 1, 5, 1), R(63, 1, 7, 1), R(78, 1, 7, 1)],
        "oscillators": [
            {"rect": R(28, 8, 2, 1), "axis": "y", "amplitude": 80, "speed": 4.0},
            {"rect": R(65, 10, 3, 1), "axis": "x", "amplitude": 120, "speed": 3.0},
            {"rect": R(42, 11, 2, 1), "axis": "y", "amplitude": 60, "speed": 4.5},
        ],
        "triggers": [
            {"trigger": R(35, 7, 2, 2), "spike": R(37, 6, 1, 1)},
            {"trigger": R(70, 4, 2, 2), "spike": R(72, 3, 1, 1)},
            {"trigger": R(90, 2, 3, 2), "spike": R(93, 1, 1, 1)},
        ],
        "axes": [
            {"pivot": R(50, 14, 1, 1)[0:2], "length": 180, "swing_degrees": 90, "speed": 2.5},
            {"pivot": R(90, 12, 1, 1)[0:2], "length": 140, "swing_degrees": 100, "speed": 3.0},
            {"pivot": R(20, 10, 1, 1)[0:2], "length": 100, "swing_degrees": 60, "speed": 4.0},
        ],
        "chasers": [
            {"spawn": R(105, 10, 1, 1)[0:2], "speed": 240.0, "max_time": 4.0},
            {"spawn": R(5, 5, 1, 1)[0:2], "speed": 180.0, "max_time": 5.0},
            {"spawn": R(60, 8, 1, 1)[0:2], "speed": 210.0, "max_time": 3.0}
        ],
        "disappear": [
             {"trigger": R(50, 8, 2, 2), "platform": R(55, 6, 8, 1)},
             {"trigger": R(15, 4, 2, 2), "platform": R(15, 3, 8, 1)}
        ],
        "crushers": [
             {"rect": R(45, 14, 2, 2), "slam_height": 450},
             {"rect": R(100, 14, 2, 2), "slam_height": 500},
             {"rect": R(115, 12, 2, 2), "slam_height": 300},
        ]
    },
    # --- Level 6: The Climb (Enhanced) ---
    {
        "id": 6, "name": "Level 6: The Climb",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(65, 14, 2, 4), 
        "platforms": [
            R(0, 1, 10, 1), 
            R(12, 3, 3, 1), R(18, 6, 3, 1), R(24, 9, 3, 1), 
            R(32, 12, 3, 1), R(45, 10, 4, 1), R(55, 14, 15, 1)
        ],
        "static_traps": [R(10, 1, 55, 1)],
        "oscillators": [
            {"rect": R(16, 8, 1, 1), "axis": "y", "amplitude": 120, "speed": 4.5}, 
            {"rect": R(30, 10, 1, 1), "axis": "x", "amplitude": 140, "speed": 3.0},
            {"rect": R(40, 12, 1, 2), "axis": "y", "amplitude": 150, "speed": 5.0}
        ],
        "triggers": [
            {"trigger": R(32, 13, 2, 2), "spike": R(34, 12, 1, 1)}, 
            {"trigger": R(55, 15, 3, 2), "spike": R(58, 14, 1, 1)}, 
            {"trigger": R(5, 2, 5, 2), "spike": R(8, 1, 1, 1)},
        ],
        "axes": [
            {"pivot": R(42, 16, 1, 1)[0:2], "length": 180, "swing_degrees": 120, "speed": 2.2},
            {"pivot": R(20, 18, 1, 1)[0:2], "length": 150, "swing_degrees": 90, "speed": 3.0},
            {"pivot": R(58, 18, 1, 1)[0:2], "length": 130, "swing_degrees": 45, "speed": 4.0}
        ],
        "chasers": [
            {"spawn": R(60, 10, 1, 1)[0:2], "speed": 250.0, "max_time": 4.0},
            {"spawn": R(15, 12, 1, 1)[0:2], "speed": 200.0, "max_time": 6.0}
        ],
        "disappear": [
            {"trigger": R(18, 7, 2, 2), "platform": R(18, 6, 3, 1)},
            {"trigger": R(32, 14, 2, 2), "platform": R(32, 12, 3, 1)}
        ],
        "crushers": [
            {"rect": R(35, 18, 2, 2), "slam_height": 500},
            {"rect": R(55, 18, 2, 2), "slam_height": 400}
        ]
    },
    # --- Level 7: Panic (Enhanced) ---
    {
        "id": 7, "name": "Level 7: Panic",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(130, 4, 2, 4),
        "platforms": [
            R(0, 1, 10, 1), 
            R(15, 3, 4, 1), R(25, 5, 4, 1), R(35, 7, 4, 1), 
            R(45, 5, 4, 1), R(55, 3, 4, 1), R(65, 1, 70, 1)
        ],
        "static_traps": [R(10, 1, 120, 1)],
        "oscillators": [
            {"rect": R(12, 5, 1, 2), "axis": "x", "amplitude": 120, "speed": 5.0},
            {"rect": R(42, 8, 1, 2), "axis": "x", "amplitude": 150, "speed": 4.5},
            {"rect": R(72, 3, 1, 2), "axis": "x", "amplitude": 180, "speed": 5.5},
            {"rect": R(100, 5, 2, 1), "axis": "y", "amplitude": 100, "speed": 4.0},
        ],
        "triggers": [
            {"trigger": R(65, 2, 5, 2), "spike": R(68, 1, 1, 1)},
            {"trigger": R(85, 2, 5, 2), "spike": R(88, 1, 1, 1)},
            {"trigger": R(105, 2, 5, 2), "spike": R(108, 1, 1, 1)},
        ],
        "axes": [
            {"pivot": R(80, 12, 1, 1)[0:2], "length": 160, "swing_degrees": 90, "speed": 2.5}
        ],
        "chasers": [
            {"spawn": R(90, 7, 1, 1)[0:2], "speed": 260.0, "max_time": 4.5},
            {"spawn": R(110, 7, 1, 1)[0:2], "speed": 280.0, "max_time": 4.0},
            {"spawn": R(40, 10, 1, 1)[0:2], "speed": 200.0, "max_time": 5.0}
        ],
        "disappear": [
             {"trigger": R(25, 6, 2, 2), "platform": R(25, 5, 4, 1)},
             {"trigger": R(45, 6, 2, 2), "platform": R(45, 5, 4, 1)},
             {"trigger": R(80, 2, 2, 2), "platform": R(65, 1, 10, 1)}
        ],
        "crushers": [
             {"rect": R(50, 14, 2, 2), "slam_height": 450},
             {"rect": R(100, 14, 2, 2), "slam_height": 500}
        ]
    },
    # --- Level 8: Precision (Enhanced) ---
    {
        "id": 8, "name": "Level 8: Precision",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(85, 6, 2, 4),
        "platforms": [
            R(0, 1, 5, 1), R(12, 3, 2, 1), R(22, 6, 2, 1), R(32, 9, 2, 1), 
            R(42, 6, 2, 1), R(52, 3, 2, 1), R(65, 5, 25, 1)
        ],
        "static_traps": [R(5, 1, 80, 1)],
        "oscillators": [
            {"rect": R(15, 8, 1, 1), "axis": "y", "amplitude": 100, "speed": 4.0},
            {"rect": R(35, 12, 1, 1), "axis": "y", "amplitude": 120, "speed": 4.5},
            {"rect": R(22, 10, 1, 1), "axis": "x", "amplitude": 80, "speed": 3.0}
        ],
        "triggers": [
            {"trigger": R(65, 6, 3, 2), "spike": R(67, 5, 1, 1)}, 
            {"trigger": R(75, 6, 3, 2), "spike": R(77, 5, 1, 1)}, 
            {"trigger": R(40, 1, 5, 1), "spike": R(42, 1, 1, 1)},
        ],
        "axes": [
            {"pivot": R(28, 14, 1, 1)[0:2], "length": 180, "swing_degrees": 60, "speed": 3.0},
            {"pivot": R(48, 14, 1, 1)[0:2], "length": 180, "swing_degrees": 60, "speed": 3.0},
            {"pivot": R(65, 12, 1, 1)[0:2], "length": 140, "swing_degrees": 100, "speed": 2.5},
        ],
        "chasers": [
            {"spawn": R(80, 10, 1, 1)[0:2], "speed": 220.0, "max_time": 4.0},
            {"spawn": R(20, 12, 1, 1)[0:2], "speed": 180.0, "max_time": 8.0}
        ],
        "disappear": [
             {"trigger": R(32, 10, 2, 2), "platform": R(32, 9, 2, 1)},
             {"trigger": R(12, 5, 2, 2), "platform": R(12, 3, 2, 1)}
        ],
        "crushers": [
             {"rect": R(28, 14, 2, 2), "slam_height": 400},
             {"rect": R(52, 14, 2, 2), "slam_height": 400}
        ]
    },
    # --- Level 9: The Gauntlet (Enhanced) ---
    {
        "id": 9, "name": "Level 9: The Gauntlet",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(125, 4, 3, 5), 
        "platforms": [
            R(0, 1, 10, 1), 
            R(15, 3, 8, 1), R(30, 6, 8, 1), R(45, 9, 8, 1),
            R(60, 6, 8, 1), R(75, 3, 8, 1), R(90, 1, 40, 1)
        ],
        "static_traps": [R(10, 1, 10, 1), R(23, 1, 15, 1), R(38, 1, 15, 1), R(53, 1, 15, 1), R(68, 1, 15, 1), R(83, 1, 15, 1)],
        "oscillators": [
            {"rect": R(45, 12, 2, 1), "axis": "y", "amplitude": 100, "speed": 4.0},
            {"rect": R(85, 12, 2, 1), "axis": "y", "amplitude": 120, "speed": 3.5},
            {"rect": R(60, 15, 2, 1), "axis": "x", "amplitude": 100, "speed": 2.5}
        ],
        "triggers": [
            {"trigger": R(30, 7, 3, 2), "spike": R(33, 6, 1, 1)},
            {"trigger": R(100, 2, 5, 2), "spike": R(105, 1, 1, 1)},
        ],
        "axes": [
            {"pivot": R(25, 15, 1, 1)[0:2], "length": 180, "swing_degrees": 90, "speed": 2.5},
            {"pivot": R(65, 15, 1, 1)[0:2], "length": 180, "swing_degrees": 120, "speed": 2.0},
            {"pivot": R(105, 15, 1, 1)[0:2], "length": 180, "swing_degrees": 180, "speed": 2.8},
        ],
        "chasers": [
            {"spawn": R(110, 14, 1, 1)[0:2], "speed": 260.0, "max_time": 4.5},
            {"spawn": R(20, 10, 1, 1)[0:2], "speed": 200.0, "max_time": 6.0},
            {"spawn": R(70, 12, 1, 1)[0:2], "speed": 240.0, "max_time": 4.0}
        ],
        "disappear": [
            {"trigger": R(45, 10, 2, 2), "platform": R(45, 9, 8, 1)},
            {"trigger": R(75, 4, 2, 2), "platform": R(75, 3, 8, 1)}
        ],
        "crushers": [
             {"rect": R(50, 16, 2, 2), "slam_height": 550},
             {"rect": R(80, 16, 2, 2), "slam_height": 500},
             {"rect": R(110, 16, 2, 2), "slam_height": 600}
        ]
    },
    # --- Level 10: Betrayal (Enhanced) ---
    {
        "id": 10, "name": "Level 10: Betrayal",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(140, 8, 2, 4), 
        "platforms": [
            R(0, 1, 12, 1), 
            R(18, 3, 4, 1), R(28, 5, 4, 1), R(38, 7, 4, 1), 
            R(50, 4, 10, 1), R(70, 6, 10, 1), R(90, 8, 10, 1),
            R(110, 3, 10, 1), R(130, 8, 20, 1)
        ],
        "static_traps": [R(12, 1, 128, 1)],
        "oscillators": [
            {"rect": R(15, 6, 1, 1), "axis": "y", "amplitude": 80, "speed": 4.0},
            {"rect": R(45, 9, 1, 1), "axis": "x", "amplitude": 100, "speed": 3.0},
            {"rect": R(110, 12, 2, 1), "axis": "y", "amplitude": 150, "speed": 5.0},
        ],
        "triggers": [
            {"trigger": R(50, 5, 3, 2), "spike": R(52, 4, 1, 1)}, 
            {"trigger": R(90, 9, 3, 2), "spike": R(92, 8, 1, 1)}, 
            {"trigger": R(130, 9, 3, 2), "spike": R(135, 8, 1, 1)},
        ],
        "axes": [
            {"pivot": R(60, 15, 1, 1)[0:2], "length": 140, "swing_degrees": 180, "speed": 1.8},
            {"pivot": R(100, 15, 1, 1)[0:2], "length": 140, "swing_degrees": 180, "speed": 2.2},
            {"pivot": R(30, 12, 1, 1)[0:2], "length": 120, "swing_degrees": 90, "speed": 3.0},
        ],
        "chasers": [
            {"spawn": R(120, 10, 1, 1)[0:2], "speed": 280.0, "max_time": 3.0},
            {"spawn": R(10, 5, 1, 1)[0:2], "speed": 220.0, "max_time": 5.0}
        ],
        "disappear": [
             {"trigger": R(38, 8, 2, 2), "platform": R(38, 7, 4, 1)},
             {"trigger": R(70, 7, 2, 2), "platform": R(70, 6, 10, 1)},
             {"trigger": R(110, 4, 2, 2), "platform": R(110, 3, 10, 1)}
        ],
        "crushers": [
             {"rect": R(50, 16, 2, 2), "slam_height": 550},
             {"rect": R(90, 16, 2, 2), "slam_height": 500}
        ]
    },
    # --- Level 11: Chaos (Enhanced) ---
    {
        "id": 11, "name": "Level 11: Chaos",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(160, 10, 2, 5),
        "platforms": [
            R(0, 1, 12, 1), 
            R(15, 4, 10, 1), R(35, 7, 10, 1), R(55, 10, 10, 1), R(75, 13, 10, 1),
            R(95, 10, 10, 1), R(115, 7, 10, 1), R(135, 4, 10, 1), R(155, 10, 20, 1)
        ],
        "static_traps": [R(10, 1, 150, 1)],
        "oscillators": [
            {"rect": R(20, 12, 2, 1), "axis": "y", "amplitude": 120, "speed": 5.0},
            {"rect": R(60, 15, 2, 1), "axis": "x", "amplitude": 150, "speed": 4.0},
            {"rect": R(100, 12, 2, 1), "axis": "y", "amplitude": 120, "speed": 5.0},
            {"rect": R(140, 15, 2, 1), "axis": "x", "amplitude": 120, "speed": 4.5},
        ],
        "triggers": [
            {"trigger": R(35, 8, 3, 2), "spike": R(37, 7, 1, 1)}, 
            {"trigger": R(135, 5, 3, 2), "spike": R(137, 4, 1, 1)}, 
            {"trigger": R(75, 14, 3, 2), "spike": R(78, 13, 1, 1)},
            {"trigger": R(95, 11, 3, 2), "spike": R(98, 10, 1, 1)},
        ], 
        "axes": [
            {"pivot": R(45, 16, 1, 1)[0:2], "length": 180, "swing_degrees": 180, "speed": 2.0},
            {"pivot": R(85, 18, 1, 1)[0:2], "length": 200, "swing_degrees": 360, "speed": 3.0},
            {"pivot": R(125, 16, 1, 1)[0:2], "length": 180, "swing_degrees": 180, "speed": 2.0},
            {"pivot": R(160, 15, 1, 1)[0:2], "length": 150, "swing_degrees": 90, "speed": 4.0},
        ],
        "chasers": [
            {"spawn": R(50, 15, 1, 1)[0:2], "speed": 280.0, "max_time": 4.0},
            {"spawn": R(140, 15, 1, 1)[0:2], "speed": 300.0, "max_time": 3.5},
            {"spawn": R(5, 10, 1, 1)[0:2], "speed": 250.0, "max_time": 6.0}
        ],
        "disappear": [
            {"trigger": R(75, 14, 2, 2), "platform": R(75, 13, 10, 1)},
            {"trigger": R(55, 11, 2, 2), "platform": R(55, 10, 10, 1)}
        ],
        "crushers": [
             {"rect": R(35, 18, 2, 2), "slam_height": 500},
             {"rect": R(115, 18, 2, 2), "slam_height": 500}
        ]
    },
    # --- Level 12: The Gatekeeper (Enhanced) ---
    {
        "id": 12, "name": "Level 12: The Gatekeeper",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(180, 8, 3, 5),
        "platforms": [
            R(0, 1, 10, 1), 
            R(15, 5, 2, 1), R(25, 8, 2, 1), R(35, 11, 2, 1), R(45, 14, 2, 1), R(55, 17, 2, 1), 
            R(80, 15, 3, 1), R(105, 12, 3, 1), R(130, 9, 3, 1), R(155, 6, 3, 1),
            R(175, 8, 30, 1)
        ],
        "static_traps": [R(10, 1, 170, 1)],
        "oscillators": [
            {"rect": R(17, 10, 2, 4), "axis": "y", "amplitude": 150, "speed": 4.0},
            {"rect": R(47, 16, 2, 4), "axis": "y", "amplitude": 150, "speed": 4.5},
            {"rect": R(90, 18, 5, 1), "axis": "x", "amplitude": 250, "speed": 3.0},
            {"rect": R(110, 20, 2, 1), "axis": "y", "amplitude": 200, "speed": 3.5}
        ],
        "triggers": [
            {"trigger": R(175, 9, 5, 2), "spike": R(180, 8, 1, 1)},
            {"trigger": R(80, 16, 3, 2), "spike": R(83, 15, 1, 1)},
        ],
        "axes": [
            {"pivot": R(140, 18, 1, 1)[0:2], "length": 250, "swing_degrees": 360, "speed": 5.0},
            {"pivot": R(160, 15, 1, 1)[0:2], "length": 200, "swing_degrees": 360, "speed": 4.0},
            {"pivot": R(60, 20, 1, 1)[0:2], "length": 180, "swing_degrees": 360, "speed": 3.0},
        ],
        "chasers": [
            {"spawn": R(5, 6, 1, 1)[0:2], "speed": 350.0, "max_time": 4.0},
            {"spawn": R(85, 15, 1, 1)[0:2], "speed": 380.0, "max_time": 3.5},
            {"spawn": R(150, 10, 1, 1)[0:2], "speed": 300.0, "max_time": 4.0}
        ],
        "disappear": [
             {"trigger": R(35, 12, 2, 2), "platform": R(35, 11, 2, 1)},
             {"trigger": R(130, 10, 2, 2), "platform": R(130, 9, 3, 1)},
             {"trigger": R(15, 6, 2, 2), "platform": R(15, 5, 2, 1)}
        ],
        "crushers": [
             {"rect": R(70, 20, 2, 2), "slam_height": 650},
             {"rect": R(150, 18, 2, 2), "slam_height": 600},
             {"rect": R(100, 18, 2, 2), "slam_height": 550},
        ]
    },
    # --- Level 13: THE BOSS (Enhanced) ---
    {
        "id": 13, "name": "BOSS: The Devil's Throne",
        "spawn": (TILE * 2, GROUND_Y - TILE * 2),
        "goal": R(200, 5, 4, 8), 
        "platforms": [
            R(0, 1, 15, 1), 
            R(20, 4, 6, 1), R(35, 8, 6, 1), R(50, 12, 6, 1), R(70, 15, 20, 1),
            R(100, 12, 10, 1), R(125, 8, 10, 1), R(150, 4, 10, 1), R(175, 1, 40, 1) 
        ],
        "static_traps": [R(15, 1, 185, 1)],
        "oscillators": [
            {"rect": R(30, 13, 2, 3), "axis": "y", "amplitude": 200, "speed": 5.0},
            {"rect": R(110, 16, 4, 1), "axis": "x", "amplitude": 300, "speed": 4.0}, 
            {"rect": R(160, 5, 2, 1), "axis": "y", "amplitude": 150, "speed": 6.0},
            {"rect": R(10, 6, 2, 1), "axis": "y", "amplitude": 40, "speed": 3.0}
        ],
        "triggers": [
            {"trigger": R(75, 16, 5, 2), "spike": R(78, 15, 1, 1)}, 
            {"trigger": R(185, 2, 5, 2), "spike": R(190, 1, 1, 1)}, 
            {"trigger": R(50, 13, 3, 2), "spike": R(53, 12, 1, 1)},
            {"trigger": R(120, 10, 3, 2), "spike": R(125, 8, 1, 1)},
        ],
        "axes": [
            {"pivot": R(120, 20, 1, 1)[0:2], "length": 250, "swing_degrees": 360, "speed": 2.5},
            {"pivot": R(150, 18, 1, 1)[0:2], "length": 220, "swing_degrees": 360, "speed": 3.0},
            {"pivot": R(40, 20, 1, 1)[0:2], "length": 180, "swing_degrees": 180, "speed": 2.0},
            {"pivot": R(180, 15, 1, 1)[0:2], "length": 140, "swing_degrees": 90, "speed": 5.0}
        ],
        "chasers": [
            {"spawn": R(60, 20, 1, 1)[0:2], "speed": 320.0, "max_time": 6.0},
            {"spawn": R(180, 5, 1, 1)[0:2], "speed": 400.0, "max_time": 4.0},
            {"spawn": R(10, 10, 1, 1)[0:2], "speed": 350.0, "max_time": 8.0},
            {"spawn": R(120, 15, 1, 1)[0:2], "speed": 380.0, "max_time": 5.0}
        ],
        "disappear": [
             {"trigger": R(50, 13, 2, 2), "platform": R(50, 12, 6, 1)},
             {"trigger": R(125, 9, 2, 2), "platform": R(125, 8, 10, 1)},
             {"trigger": R(175, 2, 2, 2), "platform": R(175, 1, 10, 1)},
             {"trigger": R(35, 10, 2, 2), "platform": R(35, 8, 6, 1)}
        ],
        "crushers": [
             {"rect": R(40, 22, 2, 2), "slam_height": 700},
             {"rect": R(90, 22, 2, 2), "slam_height": 750},
             {"rect": R(160, 22, 2, 2), "slam_height": 700},
             {"rect": R(190, 20, 2, 2), "slam_height": 600},
             {"rect": R(20, 22, 2, 2), "slam_height": 500}
        ]
    },
]


class LevelManager:
    """Creates scrolling levels with procedurally-updated hazards."""

    def __init__(self, *, level_id: int = config.DEFAULT_LEVEL_ID) -> None:
        self.current_level_index = max(0, level_id - 1) % len(LEVEL_BLUEPRINTS)
        self.level_id = LEVEL_BLUEPRINTS[self.current_level_index]["id"]
        self.platforms: List[pygame.Rect] = []
        self.static_traps: List[pygame.Rect] = []
        self.goal_rect: Optional[pygame.Rect] = None
        self.spawn_point = pygame.Vector2(0, 0)
        self.current_attempts = 0
        self.level_length = LEVEL_LENGTH
        self.oscillators: List[OscillatingHazard] = []
        self.trigger_spikes: List[TriggerSpike] = []
        self.swing_axes: List[SwingingAxe] = []
        self.chasers: List[ChasingHazard] = [] 
        self.disappearing_platforms: List[DisappearingPlatform] = [] 
        self.crushing_hazards: List[CrushingHazard] = [] 
        self.decorations: List[Dict] = []  # List of {type: 'grass'|'stone', pos: Vector2, color: tuple}

    # ------------------------------------------------------------------
    # Level construction
    # ------------------------------------------------------------------
    def load_level(self, *, index: Optional[int] = None) -> None:
        if index is not None:
            self.current_level_index = index % len(LEVEL_BLUEPRINTS)
        blueprint = LEVEL_BLUEPRINTS[self.current_level_index]
        self.level_id = blueprint["id"]
        self.spawn_point = pygame.Vector2(blueprint["spawn"])
        
        # Reset hazard lists
        self.platforms = []
        self.static_traps = []
        self.oscillators = []
        self.trigger_spikes = []
        self.swing_axes = []
        self.chasers = [] 
        self.disappearing_platforms = [] 
        self.crushing_hazards = []
        self.decorations = []
        
        # A list to store the RECTS that are meant to disappear (for updating platforms list later)
        disappearing_rects: List[pygame.Rect] = []
        
        self.platforms = [pygame.Rect(*coords) for coords in blueprint["platforms"]]
        self.static_traps = [pygame.Rect(*coords) for coords in blueprint.get("static_traps", [])]
        self.goal_rect = pygame.Rect(*blueprint["goal"])
        self.level_length = max(self.goal_rect.right + TILE, LEVEL_LENGTH)
        
        # Instantiate disappearing platforms first
        for entry in blueprint.get("disappear", []):
            target_rect = pygame.Rect(*entry["platform"])
            self.disappearing_platforms.append(
                DisappearingPlatform(
                    trigger_rect_tuple=entry["trigger"],
                    target_platform_rect=target_rect
                )
            )
            # Add the target platform to the main platforms list initially (only if not already there)
            if target_rect not in self.platforms:
                self.platforms.append(target_rect)
            disappearing_rects.append(target_rect)

        # Instantiate other dynamic hazards (unchanged)
        self.oscillators = [
            OscillatingHazard(rect_tuple=entry["rect"], axis=entry.get("axis", "y"), amplitude=entry.get("amplitude", 40), speed=entry.get("speed", 2.0))
            for entry in blueprint.get("oscillators", [])
        ]
        self.trigger_spikes = [
            TriggerSpike(trigger_rect=entry["trigger"], spike_rect=entry["spike"])
            for entry in blueprint.get("triggers", [])
        ]
        self.swing_axes = [
            SwingingAxe(pivot=entry["pivot"], length=entry.get("length", 130), swing_degrees=entry.get("swing_degrees", 45), speed=entry.get("speed", 1.8))
            for entry in blueprint.get("axes", [])
        ]
        self.chasers = [
            ChasingHazard(spawn_pos=entry["spawn"], speed=entry.get("speed", 120.0), max_time=entry.get("max_time", 3.0))
            for entry in blueprint.get("chasers", [])
        ]
        self.crushing_hazards = [
            CrushingHazard(rect_tuple=entry["rect"], slam_height=entry.get("slam_height", 400))
            for entry in blueprint.get("crushers", [])
        ]

        # 4. Sprinkle Decorations (Ghas and Pathar)
        for plat_rect in [pygame.Rect(p) for p in blueprint.get("platforms", [])]:
            num_decor = plat_rect.width // 60
            for _ in range(num_decor):
                dx = random.randint(0, plat_rect.width - 10)
                pos = pygame.Vector2(plat_rect.x + dx, plat_rect.y)
                dtype = random.choice(['grass', 'stone', 'tree'])
                
                # Colors: Darker/lighter variants of the theme
                if dtype == 'grass':
                    color = (0, random.randint(100, 200), 50) # Green-ish
                    size = random.randint(5, 12)
                elif dtype == 'stone':
                    c = random.randint(80, 120)
                    color = (c, c, c) # Grey-ish
                    size = random.randint(5, 12)
                else: # tree
                    color = (random.randint(20, 60), random.randint(80, 140), 20) # Green Canopy
                    size = random.randint(40, 80) # Height
                
                self.decorations.append({'type': dtype, 'pos': pos, 'color': color, 'size': size})
        
        self._apply_community_traps()

    def _apply_community_traps(self) -> None:
        """USER REQUEST: Community Troll Feature is DISABLED."""
        return 

    # ------------------------------------------------------------------
    # Game loop helpers
    # ------------------------------------------------------------------
    def update_hazards(self, dt: float, player_rect: pygame.Rect) -> None:
        
        # 1. Update all hazard types
        for osc in self.oscillators:
            osc.update(dt, player_rect)
        for trig in self.trigger_spikes:
            trig.update(dt, player_rect)
        for axe in self.swing_axes:
            axe.update(dt, player_rect)
        for chaser in self.chasers: 
            chaser.update(dt, player_rect)
        for crush in self.crushing_hazards:
            crush.update(dt, player_rect)
            
        # 2. Update Disappearing Platforms (CRITICAL: Removes the platform from the main list)
        for dp in self.disappearing_platforms:
            dp.update(dt, player_rect)
            if dp.is_removed:
                # Remove the actual platform rect from the platforms list
                if dp.target_platform_rect in self.platforms:
                    self.platforms.remove(dp.target_platform_rect)
                    
    def check_hazard_collision(self, rect: pygame.Rect) -> bool:
        """Checks for collision against all static and dynamic traps."""
        for trap in self.static_traps:
            if trap.colliderect(rect):
                return True
        for osc in self.oscillators:
            if osc.collides(rect):
                return True
        for trig in self.trigger_spikes:
            if trig.collides(rect):
                return True
        for axe in self.swing_axes:
            if axe.collides(rect):
                return True
        for chaser in self.chasers:
            if chaser.collides(rect):
                return True
        for crush in self.crushing_hazards:
            if crush.collides(rect):
                return True
        return False

    # ------------------------------------------------------------------
    # Attempt + rating logic
    # ------------------------------------------------------------------
    def reset_attempts(self) -> None:
        self.current_attempts = 0

    def increment_attempts(self) -> int:
        self.current_attempts += 1
        return self.current_attempts

    def calculate_star_rating(self) -> int:
        """FR4.0: Calculates stars based on attempts."""
        if self.current_attempts <= 3:
            return 3
        if self.current_attempts <= 5:
            return 2
        return 1

    def log_death(self, world_pos: pygame.Vector2) -> None:
        """Records the player death location in the database."""
        try:
            db_manager.log_death(self.level_id, int(world_pos.x), int(world_pos.y))
        except Exception as e:
            print(f"[LevelManager] Failed to log death: {e}")

    # ------------------------------------------------------------------
    # Level rotation helpers
    # ------------------------------------------------------------------
    def advance_level(self) -> None:
        self.current_level_index = (self.current_level_index + 1) % len(LEVEL_BLUEPRINTS)
        self.load_level()

    @property
    def level_number(self) -> int:
        return self.current_level_index + 1

    @property
    def level_name(self) -> str:
        return LEVEL_BLUEPRINTS[self.current_level_index]["name"]

    @property
    def total_levels(self) -> int:
        return len(LEVEL_BLUEPRINTS)

    def peek_next_level_name(self) -> str:
        next_index = (self.current_level_index + 1) % len(LEVEL_BLUEPRINTS)
        return LEVEL_BLUEPRINTS[next_index]["name"]


level_manager = LevelManager()