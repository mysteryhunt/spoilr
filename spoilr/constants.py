PUZZLE_QUEUE_LIMIT = 2
QUEUE_LIMIT = 10
CONTACT_LIMIT = 5

# ----- 2014-specific -----

DRINK_COST = [14, 24, 34]
TRAIN_COST = 90

DRINK_READY = [DRINK_COST[0],
               DRINK_COST[0] + DRINK_COST[1],
               DRINK_COST[0] + DRINK_COST[1] + DRINK_COST[2],
           ]
TRAIN_READY = [DRINK_READY[-1] + TRAIN_COST,
               DRINK_READY[-1] + TRAIN_COST + TRAIN_COST,
               DRINK_READY[-1] + TRAIN_COST + TRAIN_COST + TRAIN_COST,
]
MAX_POINTS = TRAIN_READY[-1]

POINT_INCR_MIT = 2
POINT_INCR_WL = 3
POINT_INCR_WLMETA = TRAIN_COST

WL_RELEASE_INIT = 4
