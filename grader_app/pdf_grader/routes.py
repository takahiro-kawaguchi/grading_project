from flask import Blueprint, render_template, current_app, request, url_for
from grader_app.pdf_grader.utils import get_students, get_submission, issubmitted
from flask import jsonify
import os
import grader_app.pdf_grader.utils
from grader_app.utils import load_problems_from_json, save_problems_to_json, load_grades_from_json, save_grades_to_json, check_all_grades_entered, find_next_unfinished_student, get_enrolled_students
import pandas as pd

pdf_bp = Blueprint(
    'pdf', __name__, 
    template_folder='templates', 
    static_folder='static',
    url_prefix='/pdf'
)

@pdf_bp.route('/')
def index():
    sorted_dirlist = current_app.config['PDF_LIST']
    finished = [True for report in sorted_dirlist]
    return render_template("pdf_grader/reportlist.html", dirlist=sorted_dirlist, finished=finished)

@pdf_bp.route('<int:report_index>/students/')
def student_list(report_index):
    dirlist = current_app.config['PDF_LIST']
    students = get_students(report_index)
    finished = [False for student in students]
    report = dirlist[report_index]
    return render_template("studentlist.html", student_list=students, report_index=report_index, report=report, finished=finished)

@pdf_bp.route('<int:report_index>/<int:student_index>/')
def viewer(report_index, student_index):
    rotate = request.args.get("rotate", default=0, type=int) % 4
    problems = load_problems_from_json('pdf', current_app.config['PDF_LIST'][report_index])
    grades = load_grades_from_json('pdf', current_app.config['PDF_LIST'][report_index], get_students(report_index)[student_index])
    student_names = get_students(report_index)
    next_unfinished_index, next_unfinished_name = find_next_unfinished_student(
        'pdf',
        current_app.config['PDF_LIST'][report_index],
        student_names,
        problems,
        student_index
    )
    return render_template(
        "pdf_grader/viewer.html",
        report_index=report_index,
        report_name = current_app.config['PDF_LIST'][report_index],
        student_index=student_index,
        student_name=student_names[student_index],
        total_students=len(student_names),
        back_url=url_for('pdf.viewer', report_index=report_index, student_index=student_index, rotate=rotate),
        problems=problems,
        gardes=grades,
        rotate=rotate,
        next_unfinished_index=next_unfinished_index,
    )

@pdf_bp.route('generate/<int:report_index>/<int:student_index>/<kind>/')
def generate(report_index, student_index, kind):
    report_name = current_app.config['PDF_LIST'][report_index]
    student_list = get_students(report_index)
    student_name = student_list[student_index]
    print(f"Generating images for report: {report_name}, student: {student_name}, kind: {kind}")
    if kind == "detail":
        kind_name = "詳細"
    elif kind == "answer":
        kind_name = "解答のみ"

    submission = get_submission(report_name, student_name, kind_name)
    print(submission)

    html = render_template(
        "pdf_grader/images.html",
        kind_name=kind_name,
        images=submission
    )
    return jsonify({'html': html})

@pdf_bp.route('<int:report_index>/edit_problems/')
def edit_problems(report_index):
    back_url = request.args.get('back_url', url_for('pdf.index'))
    return render_template(
        "edit_problems.html",
        report_index=report_index,
        report_name=current_app.config['PDF_LIST'][report_index],
        back_url=back_url,
        data = load_problems_from_json('pdf', current_app.config['PDF_LIST'][report_index])
    )

@pdf_bp.route('<int:report_index>/save_problems/', methods=['POST'])
def save_problems(report_index):
    try:
        client_data = request.json
        new_order = client_data['order']
        new_problems = client_data['problems']

        storage = load_problems_from_json('pdf', current_app.config['PDF_LIST'][report_index])
        
        storage['order'] = new_order
        storage['problems'] = new_problems
        
        # for student_id in storage['grades']:
        #     updated_student_grades = {}
        #     for q_id in new_order:
        #         updated_student_grades[q_id] = storage['grades'][student_id].get(q_id, None)
        #     storage['grades'][student_id] = updated_student_grades

        save_problems_to_json("pdf", current_app.config['PDF_LIST'][report_index], storage)
        return jsonify({"status": "success", "message": "保存が完了しました"}), 200
    except Exception as e:
        print(f"Error saving problems: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@pdf_bp.route('<int:report_index>/<int:student_index>/save_grades', methods=['POST'])
def save_grades(report_index, student_index):
    try:
        received = request.json
        grades = received.get('grades', {}) # {"grade_q_1": "circle", "grade_q_2": "cross", ...}

        student_name = get_students(report_index)[student_index]
        report_name = current_app.config['PDF_LIST'][report_index]
        save_grades_to_json('pdf', report_name, student_name, grades)
        finished = check_all_grades_entered(load_problems_from_json('pdf', report_name), grades)
        if finished:
            print(f"All grades entered for student: {student_name} in report: {report_name}")
            return jsonify({"status": "finished"}), 200
        else:
            return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error saving grades: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@pdf_bp.route('<int:report_index>/check_finished/')
def check_finished(report_index):
    try:
        report_name = current_app.config['PDF_LIST'][report_index]
        student_list = get_students(report_index)
        finished_status = []
        problems = load_problems_from_json('pdf', report_name)
        for student_name in student_list:
            grades = load_grades_from_json('pdf', report_name, student_name)
            finished = check_all_grades_entered(problems, grades)
            finished_status.append(finished)
        return jsonify({"finished": finished_status}), 200
    except Exception as e:
        print(f"Error checking finished status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@pdf_bp.route('<int:report_index>/check_all_finished/')
def check_all_finished(report_index):
    try:
        report_name = current_app.config['PDF_LIST'][report_index]
        student_list = get_students(report_index)
        problems = load_problems_from_json('pdf', report_name)
        all_finished = True
        for student_name in student_list:
            grades = load_grades_from_json('pdf', report_name, student_name)
            finished = check_all_grades_entered(problems, grades)
            if not finished:
                all_finished = False
                break
        return jsonify({"all_finished": all_finished}), 200
    except Exception as e:
        print(f"Error checking all finished status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@pdf_bp.route('report_status/')
def report_status():
    try:
        df_students = get_enrolled_students('pdf')
        if df_students is None:
            return jsonify({"status": "error", "message": "No enrolled student files found."}), 404
        
        df_unlisted_students = None
        report_list = current_app.config['PDF_LIST']

        for i, report_name in enumerate(report_list):
            students_names = get_students(i) # フォルダ内の学生名リスト
            status_list = {}
            name_mapping = {}
            for student_name in students_names:
                submission_detail = issubmitted(report_name, student_name, '詳細')
                submission_answer = issubmitted(report_name, student_name, '解答のみ')
                
                # 学籍番号を取得（"学籍番号 氏名" 形式を想定）
                number = student_name.split(" ")[0].upper().strip()
                name = " ".join(student_name.split(" ")[1:]).strip() if len(student_name.split(" ")) > 1 else ""
                
                if submission_detail and submission_answer:
                    status = "◎"
                elif submission_detail:
                    status = "詳"
                elif submission_answer:
                    status = "答"
                else:
                    status = "×"
                status_list[number] = status
                name_mapping[number] = name
            
            # 1. 今回の提出状況をDF化
            status_df = pd.DataFrame([
                {'学籍番号': k, '氏名': name_mapping[k], report_name: v} 
                for k, v in status_list.items()
            ])            
            # 2. 名簿本体にマージし、未提出(NaN)を "×" で埋める
            df_students = pd.merge(df_students, status_df.drop(columns=['氏名']), on='学籍番号', how='left')
            df_students[report_name] = df_students[report_name].fillna("×")
            
            # 3. 名簿外の学生を抽出
            unlisted_data = status_df[~status_df['学籍番号'].isin(df_students['学籍番号'])]
            
            if not unlisted_data.empty:
                if df_unlisted_students is None:
                    df_unlisted_students = unlisted_data
                else:
                    # 名簿外学生リスト同士をマージ（新しいレポート列を追加していく）
                    df_unlisted_students = pd.merge(df_unlisted_students, unlisted_data, on=['学籍番号','氏名'], how='outer')
        
        # 4. 最後に元の順番でソート
        df_students = df_students.sort_values('original_order')

        # 名簿外リストも NaN を "×" で埋める（必要であれば）
        if df_unlisted_students is not None:
            df_unlisted_students = df_unlisted_students.fillna("×")

        # print("--- Enrolled Students ---")
        # print(df_students.head())
        # print("--- Unlisted Students ---")
        # print(df_unlisted_students.head() if df_unlisted_students is not None else "No unlisted students")

        if df_unlisted_students is not None:
            df_unlisted_students = df_unlisted_students.fillna("×")
        context = {
            "enrolled": df_students.to_dict(orient='records'),
            "unlisted": df_unlisted_students.to_dict(orient='records') if df_unlisted_students is not None else [],
            "columns": df_students.columns.tolist()
        }

        return render_template("pdf_grader/report_status.html", **context) , 200

    except Exception as e:
        print(f"Error getting enrolled students: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500