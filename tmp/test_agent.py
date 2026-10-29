import traceback
import server
try:
    from ace_task import run_task_autonomous
    result = run_task_autonomous('open the app and go to the portal, take a screenshot', task_name='test', max_turns=10)
    print(result.summary())
except Exception as e:
    traceback.print_exc()
