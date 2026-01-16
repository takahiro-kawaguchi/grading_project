from flask import Blueprint, render_template, current_app, request
from grader_app.pdf_grader.utils import get_students, get_submission
from flask import jsonify
import os

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
    return render_template("dirlist.html", dirlist=sorted_dirlist, finished=finished)

@pdf_bp.route('<int:report_index>/students/')
def student_list(report_index):
    dirlist = current_app.config['PDF_LIST']
    students = get_students(report_index)
    finished = [False for student in students]
    report = dirlist[report_index]
    return render_template("studentlist.html", student_list=students, report_index=report_index, report=report, finished=finished)

@pdf_bp.route('<int:report_index>/<int:student_index>/')
def view_submission(report_index, student_index):
    rotate = request.args.get("rotate", default=0, type=int) % 4
    return render_template(
        "pdf_grader/viewer.html",
        report_index=report_index,
        report_name = current_app.config['PDF_LIST'][report_index],
        student_index=student_index,
        student_name=get_students(report_index)[student_index],
        total_students=len(get_students(report_index)),
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



    # pdfs = os.listdir(os.path.join(basedir, sorted_dirlist[report_index], student))
    # img_name = student
    # pdf_path_list = [os.path.join(basedir, sorted_dirlist[report_index], student, pdf) for pdf in pdfs]
    # images = convert_pdf_to_images(pdf_path_list, sorted_dirlist[report_index], img_name)
    # if rotate != 0:
    #     images = rotate_images(images, rotate)
    # marks = load_marks(sorted_dirlist[report_index], student)
    # problems = load_problem_list(sorted_dirlist[report_index])
    # myurl = f"'/pdf/{report_index}/{student_index}/{page_num}?question={question}&rotate={rotate}&v={version}'"

    # if page_num >= len(images):
    #     return "No more pages."
    

    # return render_template(
    #     "viewer.html",
    #     image_path=images[page_num],
    #     report_index=report_index,
    #     student_index=student_index,
    #     report=sorted_dirlist[report_index],
    #     student=student,
    #     page_num=page_num,
    #     total_pages=len(images),
    #     total_pdfs=len(pdfs),
    #     total_students=len(student_list),
    #     marks=marks,
    #     question=question,
    #     problems=problems,
    #     problems_num=len(problems),
    #     myurl=myurl,
    #     auto_next=auto_next,
    #     confirm_next=auto_next_check,
    #     rotate=rotate
    # )