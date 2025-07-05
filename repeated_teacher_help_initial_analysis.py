import pandas as pd
import math
from datetime import datetime
import numpy as np

def analysis(INPUT_CSV):
    df = pd.read_csv(INPUT_CSV) 
    '''
    All columns (running: print(df.columns.to_list))
    ['Anon Student Id', 'Session Id', 'Time', 'KC_Model(MATHia)',
       'Level (Section)', 'Problem Name', 'Step Name', 'Attempt At Step',
       'Help Level', 'Selection', 'Action', 'Input', 'Outcome', 'CF (Rule Id)',
       'CF (Semantic Event ID)', 'CF (Etalon)', 'CF (Skill Previous p-Known)',
       'CF (Skill New p-Known)', 'CF (Module)', 'CF (Workspace Encounter)',
       'CF (Workspace Variant)', 'CF (Workspace Progress Status)',
       'CF (Skill Opportunity)', 'cf_school_id', 'cf_class_id',
       'Selection <- ifelse(Action == "Done Button", "Done Button", NA)',
       'helpedTransaction']
    '''
    ''' 
    Session Id: anonymous identifier of the student’s login session in MATH 
    Anon Student Id: anonymous student identifier
    cf_class_id: anonymous identifier for the MATHia class to which the teach assigned the student. 
    This anonymous identifier may be used to group studen within a single MATHia class. Ranges between 0 and number of classes - 1. 
    '''
    '''
    print('Number of helped transaction: ', print(df['helpedTransaction'].value_counts()))
    '''

    ### Risk Ratio 1: across all sessions
    print("These are session with >=1 helped transaction: ")
    helped_counts_by_session = df['helpedTransaction'].groupby(df['Session Id']).sum()
    session_never_helped = helped_counts_by_session[helped_counts_by_session == 0]
    session_helped_only_once = helped_counts_by_session[helped_counts_by_session == 1]
    session_helped_at_least_once = helped_counts_by_session[helped_counts_by_session >= 1]
    session_helped_at_least_twice = helped_counts_by_session[helped_counts_by_session >= 2]
    print("\nIn ", len(session_never_helped), " session, teacher never helped: ")
    print(session_never_helped)
    print("\nIn ", len(session_helped_only_once), " session, teacher helped only once: ")
    print(session_helped_only_once)
    print("\nIn ", len(session_helped_at_least_twice), " session, teacher helped at least twice: ")
    print(session_helped_at_least_twice)

    baseline = len(session_helped_at_least_once) / len(session_never_helped)
    conditional = len(session_helped_at_least_twice) / len(session_helped_at_least_once)
    print(f"Pr(helped at least once overall) = {baseline}, Pr(helped at least twice | helped at least once overall) = {conditional}")
    print("Risk ratio = ", conditional/baseline)
    
    ### Risk Ratio 2: across all sessions for each student
    students = df['Anon Student Id'].unique().tolist()
    total_num_students = df['Anon Student Id'].nunique()
    risk_ratios = []
    risk_ratios_excluding_one_help_only = []
    for s in students:
        student_s_df = df[df['Anon Student Id'] == s]
        num_session_total_student_s = student_s_df['Session Id'].nunique()

        helped_counts_by_session = student_s_df['helpedTransaction'].groupby(student_s_df['Session Id']).sum()
        session_never_helped = helped_counts_by_session[helped_counts_by_session == 0]
        session_helped_only_once = helped_counts_by_session[helped_counts_by_session == 1]
        session_helped_at_least_once = helped_counts_by_session[helped_counts_by_session >= 1]
        session_helped_at_least_twice = helped_counts_by_session[helped_counts_by_session >= 2]

        assert(num_session_total_student_s == len(session_never_helped) + len(session_helped_at_least_once))
        #print(f"Number of sessions with (no help) {len(session_never_helped)}, (one help) {len(session_helped_only_once)}, (two or more help) {len(session_helped_at_least_twice)}")

        #if len(session_helped_at_least_twice) == 0: 
        #     print(f"There is no session with >= 2 teacher's help for student {s}.")
        if len(session_helped_at_least_once) == 0: 
            #print(f"There is no session with exact one help for student {s}.")
            continue
        if len(session_never_helped) == 0: 
            #print(f"There is no session without teacher's help for student {s}.")
            continue

        baseline = len(session_helped_at_least_once) / num_session_total_student_s
        conditional = len(session_helped_at_least_twice) / len(session_helped_at_least_once)
        print(f"For student {s}, Pr(helped at least once overall) = {baseline}, Pr(helped at least twice | helped at least once overall) = {conditional}")
        # print(f"Risk ratio = ", np.round(conditional/baseline, 2))
        if conditional/baseline != 0:
            risk_ratios_excluding_one_help_only.append(conditional/baseline)
        risk_ratios.append(conditional/baseline)

    
    print(f"Risk ratio excluding one help only case = {np.mean(np.array(risk_ratios_excluding_one_help_only))}")
    print(f"Risk ratio = {np.mean(np.array(risk_ratios))}")
        

    
    '''
    print("These are students with >=1 helped transaction: ")
    helped_counts_by_student = (df['helpedTransaction'] == True).groupby(df['Anon Student Id']).sum()
    student_never_receive_help = helped_counts_by_student[helped_counts_by_student == 0]
    student_helped_only_once = helped_counts_by_student[helped_counts_by_student == 1]

    student_helped_at_least_once = helped_counts_by_student[helped_counts_by_student >= 1]

    student_helped_at_least_twice = helped_counts_by_student[helped_counts_by_student >= 2]
    print("\nOn ", len(student_never_receive_help), " students, teacher never helped: ")
    print(student_never_receive_help)
    print("\nOn ", len(student_helped_only_once), " students, teacher helped only once: ")
    print(student_helped_only_once)
    print("\nOn ", len(student_helped_at_least_twice), " students, teacher helped at least twice: ")
    print(student_helped_at_least_twice)
    print("Conclusion 1: \nHelped transaction is much much more sparse in sessions compared to in students.\n")

    print("Only counting for number of students (regardless of classes & sessions)")
    cross_session_conditional_probability = len(student_helped_at_least_twice) / len(student_helped_at_least_once)
    print("Pr(helped again | helped at least once) = ", cross_session_conditional_probability)
    cross_session_baseline_probability = len(student_helped_at_least_once) / df['Anon Student Id'].nunique()
    print("Pr(helped at least once) = ", cross_session_baseline_probability)
    print('Risk ratio = ', cross_session_conditional_probability/cross_session_baseline_probability, '\n')
    print('Conclusion 2: Because RR > 1, students who have already been helped have higher relative “risk” of being helped again than the average first-help risk.\n')
    #print('However, this is not very insightful, because different teacher / classes may have different emphasis in helping, and a student being helped across different classes/sessions tell very little about teachers behavior, since typically teachers don't count the number of times they have helped a student.')
    '''

    '''
    print("These are classes with >=1 helped transaction: ")
    helped_counts_by_classes = (df['helpedTransaction'] == True).groupby(df['cf_class_id']).sum()
    classes_never_helped = helped_counts_by_classes[helped_counts_by_classes == 0]
    classes_helped_only_once = helped_counts_by_classes[helped_counts_by_classes == 1]
    classes_helped_at_least_once = helped_counts_by_classes[helped_counts_by_classes >= 1]
    classes_helped_at_least_twice = helped_counts_by_classes[helped_counts_by_classes >= 2]
    print("\nIn ", len(classes_never_helped), " classes, teacher never helped: ")
    print(classes_never_helped)
    print("\nIn ", len(classes_helped_only_once), " classes, teacher helped only once: ")
    print(classes_helped_only_once)
    print("\nIn ", len(classes_helped_at_least_twice), " classes, teacher helped at least twice: ")
    print(classes_helped_at_least_twice)
    print("Conclusion 3: Teacher at least helped twice in all classes.")
    '''

    ### Risk Ratio 3: for each class each student & all classes combined
    '''
    print("Investigate how many helps in one class: ")
    classes = df['cf_class_id'].unique().tolist()
    total_num_students = df['Anon Student Id'].nunique()
    num_students_across_classes = 0
    total_helped_at_least_once, total_helped_at_least_twice = 0, 0

    for i in range(len(classes)):
        c = classes[i]
        num_transact = df[df['cf_class_id'] == c]['Time'].nunique()
        num_students_in_this_class = df[df['cf_class_id'] == c]['Anon Student Id'].nunique()
        num_students_across_classes += num_students_in_this_class

        helped_df = df[df['cf_class_id'] == c]
        helped_df = helped_df[helped_df['helpedTransaction'] == 1]

        num_help = len(helped_df)
        num_students_helped = helped_df['Anon Student Id'].nunique()
        num_students_not_helped = num_students_in_this_class - num_students_helped
        
        help_times_count = helped_df['Anon Student Id'].value_counts()
        helped_at_least_once = len(help_times_count[help_times_count >= 1]) # helped_at_least_once
        baseline_probability = helped_at_least_once / num_students_in_this_class

        helped_at_least_twice= len(help_times_count[help_times_count >= 2]) # helped_at_least_twice
        conditional_probability = helped_at_least_twice/ helped_at_least_once

        risk_ratio_this_class = conditional_probability / baseline_probability
        #print(f"Pr(helped at least once) = {baseline_probability}, Pr(helped at least twice | helped at least once) = {conditional_probability}")
        print(f"Risk ratio in class {c}: ", risk_ratio_this_class)
        total_helped_at_least_once += helped_at_least_once
        total_helped_at_least_twice += helped_at_least_twice

        print(f"In class {c}, among {num_transact} transactions & {num_help} helped transactions, teacher helped {num_students_helped} students.")
        print(f"Among {num_students_in_this_class} students, {helped_at_least_once} students are helped at least once, {helped_at_least_twice} students are helped at least twice, {num_students_not_helped} students are not helped.\n")
    # print('Comment: some students can receive as many as 7 helps in a class; a considerable amount of students receive more than 1 helps in a class.')

    total_conditional = total_helped_at_least_twice / total_helped_at_least_once
    total_baseline = total_helped_at_least_once / num_students_across_classes
    print(f"In total, number of students helped at least once = {total_helped_at_least_once}, number of students helped at least twice = {total_helped_at_least_twice}")
    print(f"Total number of students in the platform = {total_num_students}, total number of students across all classes = {num_students_across_classes}")
    print(f"Pr(helped at least once overall) = {total_baseline}, Pr(helped at least twice | helped at least once overall) = {total_conditional}")
    print(f"Risk ratio overall: , {total_conditional / total_baseline}")
    '''

    

    return None

if __name__ == "__main__":
    INPUT_CSV = "./Updated_LiveLab_Modeling_Use.csv"
    # OUTPUT_CSV = "./new_struggle_res_full.csv"
    analysis(INPUT_CSV)
