{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = [
    (pkgs.python312.withPackages (python-pkgs:
      with python-pkgs; [
        pip
        autopep8
      ]))
    pkgs.uv
    pkgs.stdenv.cc.cc.lib
    ];

  shellHook = ''
    export LD_LIBRARY_PATH=${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
  '';
}
