{ pkgs, config, inputs, lib, ... }:

let
  pythonVersions = [ "2.7" "3.9" "3.10" "3.11" "3.12" "3.13" ];
  oldPythons = map
    (version: inputs.nixpkgs-python.packages.${pkgs.system}.${version})
    pythonVersions;

  # Python 2.7 test dependencies.  nixpkgs removed `python27Packages`
  # (Python 2 is end-of-life), so fetch the sdists and expose them via
  # PYTHONPATH in the py2.7 test envs below.
  py27TestDeps = pkgs.runCommand "py27-test-deps" { } ''
    mkdir -p $out
    tar -xzf ${pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/e4/85/1794da8024bfe701deac25dc61c19befd0626523665473d912d47ccb0bab/mock-3.0.0.tar.gz";
      sha256 = "d7b59735b8f9e20735cbfc49e8201df76e9c93ad25bfa2c1bbd08155d4e9c54a";
    }} -C $out
    tar -xzf ${pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz";
      sha256 = "1e61c37477a1626458e36f7b1d82aa5c9b094fa4802892072e49de9c60c4c926";
    }} -C $out
    tar -xzf ${pkgs.fetchurl {
      url = "https://files.pythonhosted.org/packages/94/4a/db842e7a0545de1cdb0439bb80e6e42dfe82aaeaadd4072f2263a4fbed23/funcsigs-1.0.2.tar.gz";
      sha256 = "a7bb0f2cf3a3fd1ab2732cb49eba4252c2af4240442415b4abce3b87022a8f50";
    }} -C $out
  '';

  py27MockPath = "${py27TestDeps}/mock-3.0.0:${py27TestDeps}/six-1.16.0:${py27TestDeps}/funcsigs-1.0.2";

  envs = [
    { name = "py27"; bin = "python2.7"; needsMock = true; }
    { name = "py39"; bin = "python3.9"; }
    { name = "py310"; bin = "python3.10"; }
    { name = "py311"; bin = "python3.11"; }
    { name = "py312"; bin = "python3.12"; }
    { name = "py313"; bin = "python3.13"; }
    { name = "pypy2"; bin = "pypy"; needsMock = true; }
    { name = "pypy3"; bin = "pypy3"; }
  ];

  # No --quiet: Python 2.7's unittest discover does not support it.
  testTasks = lib.listToAttrs (map
    (env: lib.nameValuePair "test:${env.name}" {
      description = "Run tests under ${env.bin}";
      exec = (lib.optionalString (env.needsMock or false) "PYTHONPATH=${py27MockPath} ") +
        "${env.bin} -m unittest discover --start-directory tests --top-level-directory .";
    })
    envs);
in
{
  languages.python = {
    enable = true;
    version = "3.13";
    venv.enable = true;
  };

  # ------------------------------------------------------------------
  # Dev tools + test matrix interpreters
  # ------------------------------------------------------------------
  packages = [
    pkgs.pre-commit
    pkgs.black  # Also used interacively.
    pkgs.mypy
    pkgs.python3Packages.coverage
    pkgs.pypy2  # PyPy 2.7 → bin/pypy
    pkgs.pypy3  # PyPy 3.11 → bin/pypy3
  ] ++ oldPythons;

  # ------------------------------------------------------------------
  # Shell entry point
  # ------------------------------------------------------------------
  # enterShell = ''
  #   echo "multiprocessing-logging dev environment"
  #   echo "python:  $(python --version)"
  #   echo "pre-commit: $(pre-commit --version)"
  # '';

  # ------------------------------------------------------------------
  # CI-style verification: `devenv test`
  # ------------------------------------------------------------------
  # enterTest = ''
  #     Setup test environment.
  # '';

  tasks = testTasks // {
    "test:type" = {
      description = "Run type check on code base";
      exec = "mypy";
    };

    "test:all" = {
      description = "Run the full test matrix";
      after = (map (env: "test:${env.name}") envs) ++ [ "test:type" ];
      before = [ "devenv:enterTest" ];
    };
  };
}
