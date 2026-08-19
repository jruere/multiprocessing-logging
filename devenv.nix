{ pkgs, config, inputs, ... }:

let
  pythonVersions = [ "3.9" "3.10" "3.11" "3.12" "3.13" ];
  oldPythons = map
    (version: inputs.nixpkgs-python.packages.${pkgs.system}.${version})
    pythonVersions;
in
{
  languages.python = {
    enable = true;
    version = "3.13";
    venv.enable = true;
  };

  # ------------------------------------------------------------------
  # Dev tools + tox matrix interpreters
  # ------------------------------------------------------------------
  packages = [
    pkgs.python3Packages.tox
    pkgs.pre-commit
    pkgs.black  # Also used interacively.
    pkgs.mypy
    pkgs.python3Packages.coverage
    pkgs.pypy2  # PyPy 2.7 → bin/pypy (tox `pypy` env)
    pkgs.pypy3  # PyPy 3.11 → bin/pypy3.11 (tox env needs base_python = "pypy3.11")
  ] ++ oldPythons;

  # ------------------------------------------------------------------
  # Shell entry point
  # ------------------------------------------------------------------
  # enterShell = ''
  #   echo "multiprocessing-logging dev environment"
  #   echo "python:  $(python --version)"
  #   echo "tox:     $(tox --version)"
  #   echo "pre-commit: $(pre-commit --version)"
  # '';

  # ------------------------------------------------------------------
  # CI-style verification: `devenv test`
  # ------------------------------------------------------------------
  enterTest = ''
    python -m unittest discover --quiet \
      --start-directory tests --top-level-directory .
    mypy
  '';

  # ------------------------------------------------------------------
  # Optional: full test matrix via `devenv tasks run test:all`
  # ------------------------------------------------------------------
  tasks."test:all" = {
    exec = "tox";
  };
}
