import os
import subprocess


from dotenv import load_dotenv


class Forge:
    def __init__(self, target_path=os.getcwd()):
        # Where local psql data goes, tailwind
        self.forge_tmp_dir = os.path.join(target_path, ".forge")

        try:
            self.repo_root = (
                subprocess.check_output(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=target_path,
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )
            self.forge_tmp_dir = os.path.join(self.repo_root, ".forge")
        except subprocess.CalledProcessError:
            # On Heroku, there won't be a repo, so we can't require that necessarily
            # (helps with some other scenarios too)
            self.repo_root = None

        # Load a .env if one exists in the repo root
        if self.repo_root and os.path.exists(os.path.join(self.repo_root, ".env")):
            load_dotenv(os.path.join(self.repo_root, ".env"))

        # If there's a directory named "app" right here,
        # assume that's the Django project.
        if os.path.exists(os.path.join(target_path, "app")):
            self.project_dir = os.path.join(target_path, "app")
        else:
            self.project_dir = target_path

        # Make sure the tmp dir exists
        if not os.path.exists(self.forge_tmp_dir):
            os.mkdir(self.forge_tmp_dir)

    def venv_cmd(self, executable, *args, **kwargs):
        # implement our own check without a stacktrace
        check = kwargs.pop("check", False)

        result = subprocess.run(
            [executable] + list(args),
            env={
                **os.environ,
                **kwargs.pop("env", {}),
            },
            check=False,
            cwd=kwargs.pop("cwd", None),
            **kwargs,
        )

        if check and result.returncode != 0:
            exit(result.returncode)

        return result

    def manage_cmd(self, *args, **kwargs):
        # Make sure our app is in the PYTHONPATH
        # when running manage.py commands
        kwargs["env"] = {"PYTHONPATH": self.project_dir}

        return self.venv_cmd(
            "python", self.user_or_forge_path("manage.py"), *args, **kwargs
        )

    def user_file_exists(self, filename):
        return os.path.exists(os.path.join(self.project_dir, filename))

    def user_or_forge_path(self, filename):
        if os.path.exists(os.path.join(self.project_dir, filename)):
            return os.path.join(self.project_dir, filename)
        return os.path.join(os.path.dirname(__file__), "default_files", filename)
