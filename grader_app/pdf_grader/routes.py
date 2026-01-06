from flask import Blueprint, render_template, current_app, request
from grader_app.pdf_grader.utils import get_students, get_images
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
    sorted_dirlist = current_app.config['PDF_LIST']
    students = get_students(report_index)
    finished = [False for student in students]
    report = sorted_dirlist[report_index]
    return render_template("authorlist.html", author_list=students, report_index=report_index, report=report, finished=finished)

@pdf_bp.route('<int:report_index>/<int:student_id>/')
def view_submission(report_index, student_id):
    rotate = request.args.get("rotate", default=0, type=int) % 4
    images = get_images(report_index, student_id, rotate)
    return render_template(
        "pdf_grader/viewer.html",
        image_path=images
    )
    # pdfs = os.listdir(os.path.join(basedir, sorted_dirlist[report_index], author))
    # img_name = author
    # pdf_path_list = [os.path.join(basedir, sorted_dirlist[report_index], author, pdf) for pdf in pdfs]
    # images = convert_pdf_to_images(pdf_path_list, sorted_dirlist[report_index], img_name)
    # if rotate != 0:
    #     images = rotate_images(images, rotate)
    # marks = load_marks(sorted_dirlist[report_index], author)
    # problems = load_problem_list(sorted_dirlist[report_index])
    # myurl = f"'/pdf/{report_index}/{author_index}/{page_num}?question={question}&rotate={rotate}&v={version}'"

    # if page_num >= len(images):
    #     return "No more pages."
    

    # return render_template(
    #     "viewer.html",
    #     image_path=images[page_num],
    #     report_index=report_index,
    #     author_index=author_index,
    #     report=sorted_dirlist[report_index],
    #     author=author,
    #     page_num=page_num,
    #     total_pages=len(images),
    #     total_pdfs=len(pdfs),
    #     total_authors=len(author_list),
    #     marks=marks,
    #     question=question,
    #     problems=problems,
    #     problems_num=len(problems),
    #     myurl=myurl,
    #     auto_next=auto_next,
    #     confirm_next=auto_next_check,
    #     rotate=rotate
    # )