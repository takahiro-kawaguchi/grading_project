from flask import Blueprint, render_template, current_app, request, url_for
from grader_app.pdf_grader.utils import get_students, get_submission, get_report_data_context
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
        new_points = client_data.get('points', {})

        storage = load_problems_from_json('pdf', current_app.config['PDF_LIST'][report_index])
        
        storage['order'] = new_order
        storage['problems'] = new_problems
        storage['points'] = new_points
        
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
        context = get_report_data_context(mode='status')
        if context is None:
            return jsonify({"status": "error", "message": "No enrolled student files found."}), 404
        return render_template("pdf_grader/report_overview.html", **context), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@pdf_bp.route('report_scores/')
def report_scores():
    try:
        context = get_report_data_context(mode='scores')
        if context is None:
            return jsonify({"status": "error", "message": "No enrolled student files found."}), 404
        # 必要なら別のテンプレート(report_scores.html)を呼ぶ
        return render_template("pdf_grader/report_overview.html", **context), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500