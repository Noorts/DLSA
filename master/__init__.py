from starlette.requests import Request


def monkey_path_max_file_count(default_max_files: int = 10_000, default_max_fields: int = 10_000):
    # This is a workaround because https://github.com/tiangolo/fastapi/pull/9640/files is not merged yet
    og_form = Request.form

    def new_form(self, max_files=default_max_files, max_fields=default_max_fields):
        return og_form(self, max_files=max_files, max_fields=max_fields)

    Request.form = new_form


monkey_path_max_file_count()
