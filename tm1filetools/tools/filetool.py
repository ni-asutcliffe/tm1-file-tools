# simplify API in files/__init.py__ ?
from pathlib import Path, PureWindowsPath, WindowsPath

# from tm1filetools.files.base import TM1File
from tm1filetools.files import (
    TM1AttributeCubeFile,
    TM1AttributeDimensionFile,
    TM1CfgFile,
    TM1CMAFile,
    TM1CubeFile,
    TM1DimensionFile,
    TM1RulesFile,
    TM1SubsetFile,
    TM1ViewFile,
)


class TM1FileTool:
    """
    TM1 file tool object

    """

    suffixes = [
        TM1CfgFile.suffix,
        TM1CubeFile.suffix,
        TM1DimensionFile.suffix,
        TM1RulesFile.suffix,
        TM1SubsetFile.suffix,
        TM1ViewFile.suffix,
        TM1CMAFile.suffix,
    ]

    def __init__(self, path: Path, local: bool = False):

        self._path: Path = path

        # local means the code is running on the machine the folder exists
        # this means that an absolute path in the cfg file can be used
        self._local = local

        self.config_file = self._find_config_file()

        # if we do have a config file, attempt to derive paths to logs, data etc
        self.data_path = self._get_data_path_from_cfg()

        # maybe this can all be abstracted to a single scan folder function?
        self.dim_files = self._find_dims()
        self.cube_files = self._find_cubes()
        self.rules_files = self._find_rules()
        self.cma_files = self._find_cmas()
        self.view_files = self._find_views()
        self.sub_files = self._find_subs()

    def get_model_cubes(self):

        return [c for c in self.cube_files if not c.is_control]

    def get_model_dimensions(self):

        return [d for d in self.dim_files if not d.is_control]

    def get_control_cubes(self):

        return [c for c in self.cube_files if c.is_control]

    def get_control_dimensions(self):

        return [d for d in self.dim_files if d.is_control]

    def get_attr_cubes(self):

        return [TM1AttributeCubeFile(c._path) for c in self.cube_files if c.name.find(c.attribute_prefix) == 0]

    def get_attr_dimensions(self):

        return [
            TM1AttributeDimensionFile(d._path)
            for d in self.dim_files
            if d.name.lower().find(d.attribute_prefix.lower()) == 0
        ]

    def _find_dims(self):
        """
        Returns a list of all dim file objects
        """

        return [TM1DimensionFile(d) for d in self._find_files(TM1DimensionFile.suffix)]

    def _find_cubes(self):

        return [TM1CubeFile(c) for c in self._find_files(TM1CubeFile.suffix)]

    def _find_rules(self):

        return [TM1RulesFile(r) for r in self._find_files(TM1RulesFile.suffix)]

    def _find_subs(self):

        return [
            TM1SubsetFile(
                s,
            )
            for s in self._find_files(TM1SubsetFile.suffix, recursive=True)
        ]

    def _find_views(self):

        return [
            TM1ViewFile(
                v,
            )
            for v in self._find_files(TM1ViewFile.suffix, recursive=True)
        ]

    def _find_cmas(self):

        return [TM1CMAFile(r) for r in self._find_files(TM1CMAFile.suffix, recursive=True)]

    def _find_files(self, suffix: str, recursive: bool = False, prefix: str = ""):

        return self._case_insensitive_glob(self.data_path, f"{prefix}*.{suffix}", recursive=recursive)

    def _find_config_file(self):

        cfg_file_path = next(self._case_insensitive_glob(path=self._path, pattern="tm1s.cfg"), None)

        if cfg_file_path:
            return TM1CfgFile(cfg_file_path)

        return None

    def _get_data_path_from_cfg(self):

        if not self.config_file:
            return self._path

        # need to read the data directory from the config file
        # which may be relative or absolute
        # a further complexity might be that the code is running on a different
        # OS to one where this tm1s.cfg file comes from...
        # for now, I'm going to assume this is a windows path

        data_dir = self.config_file.get_parameter("DataBaseDirectory")

        if data_dir:
            # Note, this is the 90% case
            # I can't find any details on how this parameter might look
            # with TM1 running on *nix, nor do I have much understanding
            pure_path = PureWindowsPath(data_dir)

            if pure_path.is_absolute():

                if self._local:
                    return WindowsPath(pure_path)
                # there are ways we could make an educated guess here but it's probably
                # more trouble than it's worth
                return None
            else:
                # thanks to the magic of pathlib, this seems to work cross platform :)
                # note, I've made it an absolute path, not sure this is strictly necessary
                # It does make writing a test a bit easier
                return Path.joinpath(self._path, pure_path).resolve()

        return self._path

    # def get_orphan_ruxes(self):
    #     """
    #     Return orphaned rux files
    #     """
    #     return self._get_orphans(object_ext="cub", artifact_ext="rux")

    # def get_orphan_attr_dims(self):
    #     """
    #     Return orphaned attribute dim files - i.e. a
    #     """
    #     return self._get_orphans(object_ext="dim", artifact_ext="dim", artifact_prefix=self.attr_prefix)

    # def _get_orphans(
    #     self, object_ext: str, artifact_ext: str, artifact_prefix: str = "", strip_prefix=True
    # ) -> List[str]:
    #     """
    #     Return a list of orphaned artifacts
    #     """

    #     objects = self._get_files(ext=object_ext)
    #     artifacts = self._get_files(ext=artifact_ext, prefix=artifact_prefix, strip_prefix=strip_prefix)

    #     return [a for a in artifacts if a not in objects]

    @staticmethod
    def _case_insensitive_glob(path: Path, pattern: str, recursive: bool = False):
        def either(c):
            return "[%s%s]" % (c.lower(), c.upper()) if c.isalpha() else c

        if recursive:
            return path.rglob("".join(map(either, pattern)))

        return path.glob("".join(map(either, pattern)))
