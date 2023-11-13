import os
import _turbosatorinetworkinterface as tsi
import time
from pylsl import StreamInfo, StreamOutlet

# Scripts looks for a Turbo-Satori connection, and will send rest and condition triggers to Turbo-Satori.
# Each new task period is its own condition (and therefore a new trigger).

# Note: Needs expyriment and pylsl to be pip installed.

print('Starting up script...')
print('Developed by Danielle Evenblij, 2023')
print(os.getcwd())

# TRIGGERS
# Set up trigger stream (note that you need to exactly write "TriggerStream', otherwise Aurora and Turbo-Satori won't recognize it!
info = StreamInfo(name='TriggerStream', type='Markers', channel_count=1, channel_format='int32',
                  source_id='Example')  # sets variables for object info
outlet = StreamOutlet(info)  # initialize stream.

def startTaskTrigger(triggerNr):
    outlet.push_sample(x=[
        triggerNr])  # Triggers are buggy in Turbo-satori but Aurora they work properly. (0 doesn't exist in TSI, and 1 = rest)
    print('===== Started task trigger nr.' + str(triggerNr))


def startRestTrigger():
    outlet.push_sample(x=[1])  # Rest trigger (=1)
    print('===== Started Rest trigger.')


def didTaskPeriodFinish(task_timer_s, durationTask):
    return task_timer_s >= durationTask


def didRestPeriodFinish(rest_timer_s, durationRest):
    return rest_timer_s >= durationRest


# Adjustable parameters
baseline_duration = 4  # seconds
durationRest = 10  # seconds
durationTask = 5  # seconds
nr_of_trials = 3

# Counters and timers
experimentTime_s = 0  # Time in seconds from the start of the experiment
task_trigger_counter = 2  # Let task trigger counter start from 2, because 1 is rest.
current_trial = 1  # Current trial number
task_timer_s = 0  # Timer for task period in seconds. Will reset when task period ended.
rest_timer_s = 0  # Timer for rest period in seconds. Will reset when rest period ended.

class State:  # States of the experiment
    BASELINE = 'Baseline'
    REST = 'Rest'
    TASK = 'Task'



# =============== START SCRIPT =================

# Look for a connection to turbo-satori
try:
    tsi = tsi.TurbosatoriNetworkInterface("127.0.0.1",
                                          55556)  # I had issues with port 55555 (which is TSI's default),but 55556 works.
    print("Turbo satori connection successful.")
except:
    # None found? Let the user know
    TSIconnectionFound = False
    print("============ WARNING: Turbo satori connection not found. ======================")

# Start with the baseline state
current_state = State.BASELINE

# Start the experiment
while True:

    # Print time passed and current experimental state
    print("T= " + str(experimentTime_s) + ". " + current_state)

    # Check if baseline duration has passed, then start task.
    if experimentTime_s == baseline_duration:
        current_state = State.TASK  # Switch to task period.
        startTaskTrigger(task_trigger_counter)  # Start task trigger
        task_trigger_counter += 1  # Increment task trigger counter

    # Check if rest duration has passed, then start task.
    if current_state == State.REST:
        rest_timer_s += 1  # Increment rest timer
        if didRestPeriodFinish(rest_timer_s, durationRest):
            current_state = State.TASK  # Switch to task period.
            rest_timer_s = 0  # Reset rest timer
            current_trial += 1 # Increment current trial number

            # First check if all trials have been completed.
            if current_trial > nr_of_trials:
                print("Stop the experiment.")
                break

            # Else start a new task trigger
            startTaskTrigger(task_trigger_counter)
            task_trigger_counter += 1  # Increment task trigger to start a new condition
            print("=== Trial " + str(current_trial) + " of " + str(nr_of_trials) + ".")  # Print current trial number.

    # Check if task duration has passed, then start rest.
    if current_state == State.TASK:
        task_timer_s += 1  # Increment task timer
        if didTaskPeriodFinish(task_timer_s, durationTask):
            current_state = State.REST  # Switch to rest period.
            task_timer_s = 0  # Reset task timer
            startRestTrigger()

    # Let time pass
    time.sleep(1)  # Wait for 1 second
    experimentTime_s += 1  # Increment experiment time with 1 second.
