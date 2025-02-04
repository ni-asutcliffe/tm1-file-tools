import json
from pathlib import Path

from .linecode import TM1LinecodeFile


class TM1ProcessFile(TM1LinecodeFile):
    """
    A class representation of a tm1 TI process file. A TM1 .pro file


    """

    suffix = "pro"

    # three line auto generated code where code tabs are empty
    _code_block_prefix_lines = ["", "#****Begin: Generated Statements***", "#****End: Generated Statements****"]

    _datasource_type_mapping = {"NULL": "None", "CHARACTERDELIMITED": "ASCII"}

    _type_mapping = {1: "Numeric", 2: "String"}

    def __init__(self, path: Path):

        super().__init__(path)

    def get_prolog_code(self, rstrip=True) -> list[str]:
        """
        Get a list of strings representing each line of code in the prolog

        Args:
            rstrip: Strip whitespace from end of lines (default=True)

        Returns:
            List of strings, one for each line in the prolog

        """

        linecode = 572

        return self._get_multiline_block(linecode, rstrip=rstrip)

    def get_metadata_code(self, rstrip=True) -> list[str]:
        """
        Get a list of strings representing each line of code in the metadata tab

        Args:
            rstrip: Strip whitespace from end of lines (default=True)

        Returns:
            List of strings, one for each line in the metadata tab

        """
        linecode = 573

        return self._get_multiline_block(linecode, rstrip=rstrip)

    def get_data_code(self, rstrip=True) -> list[str]:
        """
        Get a list of strings representing each line of code in the data tab

        Args:
            rstrip: Strip whitespace from end of lines (default=True)

        Returns:
            List of strings, one for each line in the data tab

        """

        linecode = 574

        return self._get_multiline_block(linecode, rstrip=rstrip)

    def get_epilog_code(self, rstrip=True) -> list[str]:
        """
        Get a list of strings representing each line of code in the epilog

        Args:
            rstrip: Strip whitespace from end of lines (default=True)

        Returns:
            List of strings, one for each line in the epilog

        """

        linecode = 575

        return self._get_multiline_block(linecode, rstrip=rstrip)

    def _to_json(self, sort_keys: bool = True, rstrip: bool = True):

        name = self._parse_single_string(self._get_line_by_code(602))

        prolog = self._codeblock_to_json_str(self.get_prolog_code())
        metadata = self._codeblock_to_json_str(self.get_metadata_code())
        data = self._codeblock_to_json_str(self.get_data_code())
        epilog = self._codeblock_to_json_str(self.get_epilog_code())

        security_access = self._parse_single_int(self._get_line_by_code(1217))
        security_access = security_access == 1

        parameters = self._get_parameters()
        variables = self._get_variables()

        datasource = self._get_datasource()

        json_dump = {
            "Name": name,
            "PrologProcedure": prolog,
            "MetadataProcedure": metadata,
            "DataProcedure": data,
            "EpilogProcedure": epilog,
            "HasSecurityAccess": security_access,
            "Parameters": parameters,
            "Variables": variables,
            "DataSource": datasource,
        }

        return json.dumps(json_dump, sort_keys=sort_keys, indent=4)

    def _get_parameters(self) -> list:

        # What does the json look like with no params?
        params = []

        # param names are from 560
        # param datatypes are from 561
        # param default values are from 590
        # param hints are from 637

        # this needs to be refactored
        idx_datatype = self._get_line_index_by_code(561)
        idx_default = self._get_line_index_by_code(590)
        idx_hint = self._get_line_index_by_code(637)

        names = self._get_multiline_block(linecode=560)

        for idx, name in enumerate(names):

            # these are single ints on the line
            datatype = self._type_mapping[int(self._get_line_by_index(idx_datatype + idx + 1))]

            hint = self._get_key_value_pair_string(self._get_line_by_index(idx_hint + idx + 1))["value"]

            default = self._get_key_value_pair_string(self._get_line_by_index(idx_default + idx + 1))["value"]

            params.append(
                {
                    "Name": name,
                    "Prompt": hint,
                    "Type": datatype,
                    "Value": default,
                }
            )

        return params

    def _get_variables(self) -> list:

        # Variables are a bit like the parameters with them
        # being defined over multiple lines in different sections

        # What does the json look like with no datasource?
        variables = []

        # variable names are from 577
        names = self._get_multiline_block(linecode=577)

        # offsets are from 579
        idx_offset = self._get_line_index_by_code(579)

        # types are from 578
        idx_types = self._get_line_index_by_code(578)

        # start and end bytes
        idx_start = self._get_line_index_by_code(580)
        idx_end = self._get_line_index_by_code(581)

        for idx, name in enumerate(names):

            # these are single ints on the line
            offset = int(self._get_line_by_index(idx_offset + idx + 1))
            type = self._type_mapping[int(self._get_line_by_index(idx_types + idx + 1))]

            # get start and end bytes
            start = int(self._get_line_by_index(idx_start + idx + 1))
            end = int(self._get_line_by_index(idx_end + idx + 1))

            #
            var = {"EndByte": end, "Name": name, "Position": offset, "StartByte": start, "Type": type}

            variables.append(var)

        return variables

    def _get_datasource(self) -> dict:

        # On processes with a datasource, the correct json
        # seems to be this
        datasource = {"Type": "None"}

        # need to come up with a mapping for all types
        datasource_type = self._parse_single_string(self._get_line_by_code(562))

        datasource_type_json = self._datasource_type_mapping[datasource_type]
        if datasource_type_json:
            datasource["Type"] = datasource_type_json

        # if we didn't find a mapping, return an empty datasource dict
        if datasource["Type"] == "None":
            return datasource

        # I'm going to assume the delimiter type is always "Character" when source type is ASCII
        # obviously need to map other types if necessary
        if datasource_type_json == "ASCII":
            datasource["asciiDelimiterType"] = "Character"

        datasource["asciiDecimalSeparator"] = self._parse_single_string(self._get_line_by_code(588))
        datasource["asciiDelimiterChar"] = self._parse_single_string(self._get_line_by_code(567))

        datasource["asciiHeaderRecords"] = self._parse_single_int(self._get_line_by_code(569))
        datasource["asciiQuoteCharacter"] = self._parse_single_string(self._get_line_by_code(568))
        datasource["asciiThousandSeparator"] = self._parse_single_string(self._get_line_by_code(589))
        datasource["dataSourceNameForClient"] = self._parse_single_string(self._get_line_by_code(585))
        datasource["dataSourceNameForServer"] = self._parse_single_string(self._get_line_by_code(586))

        return datasource

    @staticmethod
    def _codeblock_to_json_str(lines: list[str]) -> str:

        # how portable is this?
        newline = "\r\n"

        json_str: str = ""
        for line in lines:
            json_str = json_str + line + newline

        return json_str.removesuffix(newline)
