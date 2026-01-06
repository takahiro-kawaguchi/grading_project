from grader_app import create_app

app = create_app()

if __name__ == '__main__':
    # デバッグモードをONにすると、コード変更が即反映されます
    app.run(debug=True, port=5000)