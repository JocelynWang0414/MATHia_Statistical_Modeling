import pandas as pd
from datetime import datetime

config = {}
config['error_threshold'] = 2
config['new_step_threshold'] = 1
config['sense_of_what_to_do_threshold'] = 0.6
config['familiarity_threshold'] = 0.4
config['window_size'] = 10
config['hint_threshold'] = 6
config['system_misuse_threshold'] = 8 #
config['students_doing_well_threshold'] = 9 # 9 correct in 10 window size
config['idle_threshold'] = 5 # idle for >= 5 min
config['struggle_mastery_threshold'] = 0.8 # mastery threshold
config['struggle_num_attempts_threshold'] = 3 # attempt >= 3 times

# calculations
def is_deliberate_function(last_action, last_transaction, this_transaction):
    # Ensure Timestamp objects are converted to datetime
    time_format = "%Y-%m-%d %H:%M:%S"
    last_time = last_transaction['Time']
    this_time = this_transaction['Time']
    last_time = last_time.to_pydatetime() if isinstance(last_time, pd.Timestamp) else datetime.strptime(last_time, time_format)
    this_time = this_time.to_pydatetime() if isinstance(this_time, pd.Timestamp) else datetime.strptime(this_time, time_format)

    seconds_since_last_action = int((this_time - last_time).total_seconds())

    if last_action == 'error':
        return seconds_since_last_action > config['error_threshold']
    elif last_action in ['initial_hint', 'hint_level_change']:  # Fix logical mistake
        return seconds_since_last_action > config['hint_threshold']
    return seconds_since_last_action > config['new_step_threshold']

    # seconds_since_last_action = int((datetime.strptime(this_transaction['Time'], "%Y-%m-%d %H:%M:%S") - datetime.strptime(last_transaction['Time'], "%Y-%m-%d %H:%M:%S")).total_seconds())
    # if last_action == 'error': return seconds_since_last_action > config['error_threshold']
    # elif last_action == 'initial_hint' or 'hint_level_change': return seconds_since_last_action > config['hint_threshold'] # improvement: from calculated hint_threshold to pre-defined hint threshold
    # return seconds_since_last_action > config['new_step_threshold']

def seen_all_hint_levels_function(this_transaction):
    return True if this_transaction['Help Level'] == 4 else False

def sense_of_what_to_do_function(this_transaction):

    # Jocelyn: need the [p_know] for all skills in rawSkills to be above the senseOfWhatToDoThreshold
    return this_transaction['CF (Skill New p-Known)'] > config['sense_of_what_to_do_threshold']

def is_low_skill_step_some_function(this_transaction):
    return this_transaction['CF (Skill New p-Known)'] <= config['familiarity_threshold']

def is_familiar_function(this_transaction):
    return this_transaction['CF (Skill New p-Known)'] > config['familiarity_threshold']

def evaluate_action(last_transaction, this_transaction):
    last_action = last_transaction['Outcome'].lower() # hint or others
    is_correct = (this_transaction['Outcome'].lower() == "ok")
    last_action_is_error, last_action_is_hint, last_action_unclear_fix = (last_action == "error"), (last_action == 'initial_hint' or 'hint_level_change'), (last_action == 'jit')

    seen_all_hint_levels = seen_all_hint_levels_function(this_transaction)
    is_deliberate = is_deliberate_function(last_action, last_transaction, this_transaction)

    # BKT based parameters
    sense_of_what_to_do = sense_of_what_to_do_function(this_transaction)
    is_low_skill_step_some = is_low_skill_step_some_function(this_transaction)
    is_familiar = is_familiar_function(this_transaction)

    if this_transaction['Outcome'].lower() == "hint":
        print("isHint")
        if is_deliberate:
            print("isDeliberate")
            if is_low_skill_step_some and not last_action_is_error:
                return "not acceptable/asked hint on low skill step"
            else:
                if not seen_all_hint_levels and (not is_familiar or (last_action_is_error and last_action_unclear_fix) or last_action_is_hint):
                    return "preferred/ask hint"
                elif is_familiar and not sense_of_what_to_do or last_action_is_hint:
                    return "acceptable/ask hint"
                else:
                    return "hint abuse"
        else:
            print("not deliberate")
            return "hint abuse"

    else:
        if is_low_skill_step_some and not last_action_is_error:
            return "preferred/try step on low skill step"
        else:
            if is_deliberate:
                if (is_familiar and not (last_action_is_error and last_action_unclear_fix)) or (
                        last_action_is_hint):
                    return "preferred/try step"
                elif seen_all_hint_levels and not (last_action_is_error and last_action_unclear_fix):
                    return "preferred/try step"
                elif is_correct:
                    return "acceptable/try step"
                elif seen_all_hint_levels:
                    if last_action_is_error and last_action_unclear_fix:
                        return "ask teacher for help"
                else:
                    return "hint avoidance"
            else:
                return "not deliberate"

def is_not_deliberate(help_model_output): return help_model_output == "not deliberate"
def is_gaming(help_model_output): return False
def is_abusing_hints(help_model_output): return help_model_output == "hint abuse"

def calculate_status_system_misuse(df, threshold):
    status, window, window_size = [], [], 10
    for i in range(len(df)):
        outcome = df['Outcome'].iloc[i]  # mostly OK, ERROR, INITIAL_HINT, JIT, HINT_LEVEL_CHANGE
        model_output = evaluate_action(df.iloc[i - 1], df.iloc[i])
        # Add to attempt window based on is gaming, is abusing hints, and is not deliberate
        attemptCorrect = 1 if is_abusing_hints(model_output) or is_not_deliberate(model_output) else 0
        window.append(attemptCorrect)
        # Check length fixed
        if len(window) == window_size: window.pop(0)
        # System_misuse window detection logic
        status.append(True) if sum(window) >= threshold else status.append(False)
    return status

def calculate_status_students_doing_well(df, threshold):

    status, window, window_size = [], [], 10
    for i in range(len(df)):
        # Add to attempt window based on action correct
        attemptCorrect = 1 if df['Outcome'].iloc[i].lower() == "ok" else 0
        window.append(attemptCorrect)
        # Check length fixed
        if len(window) == window_size: window.pop(0)
        # Students_doing_well detection logic
        if sum(window) >= threshold:
          status.append(True)
        else: status.append(False)
    return status

# CSV processing
def process_csv(input_csv, output_csv):
    original_df = pd.read_csv(input_csv)
    
    original_df["Time"] = pd.to_datetime(original_df["Time"])

    df_unique_pairs = original_df[['Anon Student Id', 'Session Id', 'Problem Name']].drop_duplicates()

    processed_df_list = []
    for index in range(len(df_unique_pairs)):
        if index % 1000 == 0: print(index)
        student_id, session_id, problem_name = df_unique_pairs.iloc[index]
        df = original_df[(original_df['Anon Student Id'] == student_id)]
        df = df[df['Session Id'] == session_id]
        df = df[df['Problem Name'] == problem_name]
        df = df.sort_values(by=["Session Id", "Time"]).reset_index(drop=True)

        all_flags_misuse, all_flags_doing_well = [], []

    
        for session, group in df.groupby("Session Id", sort=False):
            group = group.copy()
            flags_misuse = calculate_status_system_misuse(group, config['system_misuse_threshold'])
            flags_doing_well = calculate_status_students_doing_well(group, config['students_doing_well_threshold'])
            all_flags_misuse.extend(flags_misuse)
            all_flags_doing_well.extend(flags_doing_well)
        
        df["System Misuse"] = all_flags_misuse
        df['Student Doing Well'] = flags_doing_well
        processed_df_list.append(df)

    final_df = pd.concat(processed_df_list, ignore_index=True)
    final_df.to_csv(output_csv, index=False)
    print(f"Student system misuse applied. Output written to {output_csv}")


if __name__ == "__main__":
    # Change these file names as desired.
    INPUT_CSV = "./new_crit_struggle_and_struggle_res_full.csv"
    OUTPUT_CSV = "./four_detectors_data.csv"
    process_csv(INPUT_CSV, OUTPUT_CSV)