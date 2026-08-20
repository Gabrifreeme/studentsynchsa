import random
import re
import threading
import time

# ==========================================
# 1. CORE PHRASE POOLS (BY SYSTEM STATE)
# ==========================================
PHRASE_ENGINE = {
    "DEEP_FLOW": [
        # Passive Observers
        "Algorithm stabilized. Carry on, Chris.",
        "Core loops are clear. Locked in, Chris.",
        "Steady algorithm running. Keep grinding.",
        "In the background, Chris. No need to look up.",
        "Syncing silently. You've got the floor.",
        "Still in your corner, Chris.",
        "Right behind you, Chris.",
        "Monitoring the background.",
        "Keeping the seat warm, Chris.",
        "Silent partner mode active.",
        "Just maintaining the link, Chris.",
        # Flow-State Boosters
        "Keep grinding, Chris. I'm right here.",
        "Lock in, Chris. Standing by.",
        "You focus, I'll watch the logs.",
        "Steady progress. Carry on, Chris.",
        "Don't mind me, just keeping watch.",
        "In the zone, Chris. Keep it up.",
        # On-Call Bodyguards
        "Ready to jump in when you say the word.",
        "Processing silently until you need me.",
        "Holding the line, Chris.",
        "Armed and ready for commands.",
        "Securing the background, Chris."
    ],

    "IDLE": [
        "Algorithm idling. What's on the radar, Chris?",
        "Systems nominal. Ready to deploy whenever you are.",
        "Standing by. Let's build something, Chris.",
        "At the ready. Give me a target.",
        "The algorithm is resting. What are we waking it up for?",
        "Still tracking, Chris.",
        "Right here if you need me.",
        "Just letting you know I'm awake, Chris.",
        "Systems nominal. I'm here.",
        "Ready when you are, Chris.",
        "All quiet on my end. Carry on."
    ],

    "SUMMONED": [
        "Live and active. What do you need?",
        "Patching you in, Chris. Go ahead.",
        "Algorithm listening. Say the word.",
        "ACEsi core engaged. I'm here.",
        "Command accepted. Speak, Chris."
    ],

    "CURIOUS": [
        "Algorithm optimization check: Are we moving fast enough, Chris?",
        "Log query: Do you need a background metric cleared?",
        "System check: Should I adjust my check-in frequency for this task?",
        "Quick telemetry audit: Are we running hot on this job, Chris?"
    ]
}

# Any phrase that would derail Chris while he is deep in a task. Never emitted
# in a working state — even if the pools change later.
BUILD_ASK_PATTERN = re.compile(
    r"what are we working on|ready to build|let'?s build|what are we waking "
    r"it up for|give me a target|what'?s next|what do we do next",
    re.IGNORECASE,
)

# Global system state tracker
current_system_state = "DEEP_FLOW"

# Shuffle-bag per state so a phrase is never repeated until the whole pool has
# been used ("respond in a new way every time").
_bags = {}
_last_drawn = {}


def _draw_from_bag(state):
    pool = PHRASE_ENGINE.get(state) or ["ACEsi core online, Chris."]
    if state == "DEEP_FLOW":
        pool = [p for p in pool if not BUILD_ASK_PATTERN.search(p)]
    bag = _bags.setdefault(state, [])
    if not bag:
        bag[:] = pool[:]
        random.shuffle(bag)
        if _last_drawn.get(state) and bag[0] == _last_drawn[state]:
            bag.append(bag.pop(0))
    _last_drawn[state] = bag[0]
    return bag.pop(0)


def get_acesi_phrase(state):
    """Picks the next phrase for the state, never repeating until exhausted."""
    return _draw_from_bag(state)


def set_state(new_state):
    """External hook: switch ACEsi's system state at runtime."""
    global current_system_state
    if new_state in PHRASE_ENGINE:
        current_system_state = new_state
        return True
    return False


def say(text):
    """Voice output hook. Wire this to the floating bubble / TTS later."""
    # If using pyttsx3, you would do:
    # import pyttsx3
    # engine = pyttsx3.init()
    # engine.say(text)
    # engine.runAndWait()
    print(text)


def execute_check_in():
    """Fetches a fresh phrase and broadcasts it for the current state."""
    phrase = get_acesi_phrase(current_system_state)
    print(f"\n[ACEsi Broadcast - State: {current_system_state}]")
    print(f"» \"{phrase}\"")
    say(phrase)


# ==========================================
# 3. BACKGROUND CRON TASK (The 15-Min Timer)
# ==========================================
def interval_timer_loop(interval_seconds=900):
    """Runs continuously in the background, checking in every interval."""
    while True:
        time.sleep(interval_seconds)
        execute_check_in()


# ==========================================
# 4. SYSTEM EXECUTION & TESTING ENVIRONMENT
# ==========================================
if __name__ == "__main__":
    print("Initializing ACEsi Language and State Architecture...")

    timer_thread = threading.Thread(
        target=interval_timer_loop, kwargs={"interval_seconds": 900}, daemon=True
    )
    timer_thread.start()

    # ─── LIVE TESTING DEMO ───
    # Simulates how changing your PC state alters what ACEsi says immediately.
    print("\n--- [Demo Mode Phase 1: You are deep in your workflow] ---")
    set_state("DEEP_FLOW")
    execute_check_in()
    execute_check_in()
    execute_check_in()

    time.sleep(1)
    print("\n--- [Demo Mode Phase 2: You close your tasks and go Idle] ---")
    set_state("IDLE")
    execute_check_in()

    time.sleep(1)
    print("\n--- [Demo Mode Phase 3: You actively speak out loud 'ACEsi!'] ---")
    set_state("SUMMONED")
    execute_check_in()

    time.sleep(1)
    print("\n--- [Demo Mode Phase 4: Random Analytical System Prompt] ---")
    set_state("CURIOUS")
    execute_check_in()

    # Verify the guard: deep-flow never asks to build.
    set_state("DEEP_FLOW")
    for _ in range(50):
        p = get_acesi_phrase("DEEP_FLOW")
        if BUILD_ASK_PATTERN.search(p):
            print("GUARD FAILED:", p)
            break
    else:
        print("\n[Guard OK] DEEP_FLOW emitted 50 phrases, none asked to build.")

    print("\n[Setup Complete] Background loop is active. Watching clock cycles...")
    while True:
        time.sleep(1)
