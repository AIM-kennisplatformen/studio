{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = [
    (pkgs.python312.withPackages (python-pkgs:
      with python-pkgs; [
        pip
        ruff
      ]))
    pkgs.stdenv.cc.cc.lib
  ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
    python3 -m venv .venv
    source .venv/bin/activate
  '';
}
