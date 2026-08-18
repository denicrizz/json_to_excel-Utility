import json
import re
from pathlib import Path
from collections import defaultdict


# ============================================================
# KONFIGURASI
# ============================================================

TEMPLATE_FILE = "template.json"

INPUT_DIR = Path("data_hasil_parsing")

OUTPUT_FILE = "data_clean.json"

MAX_FILES = 50


# ============================================================
# LOAD JSON
# ============================================================

def load_json(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# PARSE JSON
# ============================================================

def parse_json(value):

    # Sudah berupa object
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return {}

    try:

        return json.loads(value)

    except json.JSONDecodeError:

        return value


# ============================================================
# CLEAN STRING
# ============================================================

def clean_string(value):

    return re.sub(
        r"\s+",
        " ",
        value.strip()
    )


# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(value):

    if value is None:
        return None


    # STRING
    if isinstance(
        value,
        str
    ):

        return clean_string(
            value
        )


    # NUMBER / BOOLEAN
    if isinstance(
        value,
        (int, float, bool)
    ):

        return value


    # LIST
    if isinstance(
        value,
        list
    ):

        return [
            clean_value(item)
            for item in value
        ]


    # DICTIONARY
    if isinstance(
        value,
        dict
    ):

        return {
            key: clean_value(val)
            for key, val in value.items()
        }


    return value


# ============================================================
# CEK DROPDOWN
# ============================================================

def is_dropdown(value):

    if not isinstance(
        value,
        list
    ):

        return False


    if not value:

        return False


    return all(
        isinstance(
            item,
            dict
        )
        and (
            "value" in item
            or "label" in item
        )
        for item in value
    )


# ============================================================
# PARSE DATAKEY
#
# contoh:
#
# nama_usaha
# nama_usaha#1
# nama_usaha#2
# ============================================================

def parse_data_key(data_key):

    if not isinstance(
        data_key,
        str
    ):

        return data_key, None


    match = re.match(
        r"^(.*?)#(\d+)$",
        data_key
    )


    if match:

        return (
            match.group(1),
            int(match.group(2))
        )


    return data_key, None


# ============================================================
# CARI BLOK TYPE:1 DARI TEMPLATE
# ============================================================

def find_blocks(template):

    blocks = []


    def walk(obj):

        if isinstance(
            obj,
            dict
        ):

            # --------------------------------------------
            # BLOK TYPE 1
            # --------------------------------------------

            if obj.get("type") == 1:

                block = {

                    "name": obj.get(
                        "label",
                        obj.get(
                            "dataKey",
                            "Unknown"
                        )
                    ),

                    "dataKey": obj.get(
                        "dataKey"
                    ),

                    "fields": []
                }


                collect_fields(
                    obj,
                    block
                )


                blocks.append(
                    block
                )

                return


            # --------------------------------------------
            # LANJUT TELUSURI
            # --------------------------------------------

            for value in obj.values():

                if isinstance(
                    value,
                    (dict, list)
                ):

                    walk(value)


        elif isinstance(
            obj,
            list
        ):

            for item in obj:

                walk(item)


    # ========================================================
    # COLLECT DATAKEY DALAM BLOK
    # ========================================================

    def collect_fields(
        obj,
        block
    ):

        if isinstance(
            obj,
            dict
        ):

            data_key = obj.get(
                "dataKey"
            )


            # Jangan memasukkan dataKey
            # milik blok itu sendiri

            if (
                data_key
                and data_key != block["dataKey"]
                and obj.get("type") != 1
            ):

                if data_key not in block[
                    "fields"
                ]:

                    block[
                        "fields"
                    ].append(
                        data_key
                    )


            # --------------------------------------------
            # CARI CHILD
            # --------------------------------------------

            for value in obj.values():

                if isinstance(
                    value,
                    (dict, list)
                ):

                    collect_fields(
                        value,
                        block
                    )


        elif isinstance(
            obj,
            list
        ):

            for item in obj:

                collect_fields(
                    item,
                    block
                )


    walk(template)

    return blocks


# ============================================================
# MAPPING DATAKEY → BLOK
# ============================================================

def create_mapping(blocks):

    mapping = {}


    for block in blocks:

        for field in block[
            "fields"
        ]:

            base_key, _ = parse_data_key(
                field
            )


            mapping[
                base_key
            ] = block[
                "name"
            ]


    return mapping


# ============================================================
# TAMBAH VALUE KE ROW
# ============================================================

def add_value(
    row,
    key,
    value
):

    value = clean_value(
        value
    )


    # ========================================================
    # DROPDOWN
    # ========================================================

    if is_dropdown(value):

        values = []

        labels = []


        for item in value:

            if item.get(
                "value"
            ) is not None:

                values.append(
                    str(
                        item.get(
                            "value"
                        )
                    )
                )


            if item.get(
                "label"
            ) is not None:

                labels.append(
                    str(
                        item.get(
                            "label"
                        )
                    )
                )


        row[
            f"{key}_value"
        ] = ", ".join(
            values
        )


        row[
            f"{key}_label"
        ] = ", ".join(
            labels
        )


        return


    # ========================================================
    # NESTED OBJECT
    #
    # Jangan masukkan dict/list ke cell.
    # Akan diproses oleh nested handler.
    # ========================================================

    if isinstance(
        value,
        (dict, list)
    ):

        return


    # ========================================================
    # DATA NORMAL
    # ========================================================

    row[
        key
    ] = value


# ============================================================
# EXTRACT DATA DARI ANSWER JSON
# ============================================================

def extract_data(source):

    root = source.get(
        "data",
        {}
    )


    if not isinstance(
        root,
        dict
    ):

        return (
            None,
            {},
            [],
            []
        )


    # ========================================================
    # ASSIGNMENT ID
    # ========================================================

    assignment_id = root.get(
        "_id"
    )


    # ========================================================
    # PRINCIPAL DATA
    #
    # Hanya scalar.
    #
    # dict/list TIDAK dimasukkan ke principal
    # karena akan diproses sebagai nested.
    # ========================================================

    principal = {}


    for key, value in root.items():

        # data.data dan pre_defined_data
        # diproses secara terpisah

        if key in (
            "data",
            "pre_defined_data"
        ):

            continue


        # ----------------------------------------------------
        # HANYA DATA SCALAR
        # ----------------------------------------------------

        if isinstance(
            value,
            (dict, list)
        ):

            continue


        principal[
            key
        ] = clean_value(
            value
        )


    # --------------------------------------------------------
    # IDENTIFIER UTAMA
    # --------------------------------------------------------

    principal[
        "assignment_id"
    ] = assignment_id


    # ========================================================
    # PREDEFINED DATA
    # ========================================================

    predefined = parse_json(
        root.get(
            "pre_defined_data"
        )
    )


    predata = []


    if isinstance(
        predefined,
        dict
    ):

        predata = predefined.get(
            "predata",
            []
        )


    # ========================================================
    # DATA.DATA
    # ========================================================

    form_data = parse_json(
        root.get(
            "data"
        )
    )


    answers = []


    if isinstance(
        form_data,
        dict
    ):

        answers = form_data.get(
            "answers",
            []
        )


    return (
        assignment_id,
        principal,
        predata,
        answers
    )


# ============================================================
# PROSES SATU FILE
# ============================================================

def process_file(
    file_path,
    field_mapping
):

    source = load_json(
        file_path
    )


    (
        assignment_id,
        principal,
        predata,
        answers
    ) = extract_data(
        source
    )


    # ========================================================
    # TABLE NORMAL
    # ========================================================

    main_rows = defaultdict(
        dict
    )


    # ========================================================
    # TABLE NESTED
    # ========================================================

    nested_rows = defaultdict(
        lambda: defaultdict(dict)
    )


    # ========================================================
    # PROSES NESTED OBJECT
    # ========================================================

    def process_nested_object(
        table_name,
        key,
        value
    ):

        # ====================================================
        # DICTIONARY
        # ====================================================

        if isinstance(
            value,
            dict
        ):

            # -----------------------------------------------
            # Cek apakah dictionary berisi index:
            #
            # {
            #     "1": {...},
            #     "2": {...}
            # }
            # -----------------------------------------------

            numeric_keys = (
                bool(value)
                and all(
                    str(k).isdigit()
                    for k in value.keys()
                )
            )


            # =================================================
            # DICTIONARY INDEXED
            # =================================================

            if numeric_keys:

                for index, nested_data in value.items():

                    identifier = (
                        f"{assignment_id}"
                        f"#{index}"
                    )


                    nested_table_name = (
                        f"{table_name} nested"
                    )


                    row = nested_rows[
                        nested_table_name
                    ][
                        str(index)
                    ]


                    row[
                        "identifier"
                    ] = identifier


                    row[
                        "assignment_id"
                    ] = assignment_id


                    row[
                        "nested_index"
                    ] = int(index)


                    # -----------------------------------------
                    # Isi data scalar
                    # -----------------------------------------

                    if isinstance(
                        nested_data,
                        dict
                    ):

                        for (
                            child_key,
                            child_value
                        ) in nested_data.items():

                            # Nested lagi → jangan masukkan
                            if isinstance(
                                child_value,
                                (dict, list)
                            ):

                                # proses lagi sebagai nested
                                process_nested_object(
                                    table_name,
                                    child_key,
                                    child_value
                                )

                                continue


                            add_value(
                                row,
                                child_key,
                                child_value
                            )


                return


            # =================================================
            # DICTIONARY BIASA
            # =================================================

            for (
                child_key,
                child_value
            ) in value.items():

                if isinstance(
                    child_value,
                    (dict, list)
                ):

                    process_nested_object(
                        table_name,
                        child_key,
                        child_value
                    )


        # ====================================================
        # LIST
        # ====================================================

        elif isinstance(
            value,
            list
        ):

            for index, item in enumerate(
                value,
                start=1
            ):

                # ---------------------------------------------
                # Hanya object yang dijadikan row
                # ---------------------------------------------

                if isinstance(
                    item,
                    dict
                ):

                    nested_table_name = (
                        f"{table_name} nested"
                    )


                    row = nested_rows[
                        nested_table_name
                    ][
                        str(index)
                    ]


                    row[
                        "identifier"
                    ] = (
                        f"{assignment_id}"
                        f"#{index}"
                    )


                    row[
                        "assignment_id"
                    ] = assignment_id


                    row[
                        "nested_index"
                    ] = index


                    for (
                        child_key,
                        child_value
                    ) in item.items():

                        if isinstance(
                            child_value,
                            (dict, list)
                        ):

                            # nested lebih dalam
                            process_nested_object(
                                table_name,
                                child_key,
                                child_value
                            )

                            continue


                        add_value(
                            row,
                            child_key,
                            child_value
                        )


                else:

                    # list scalar
                    nested_table_name = (
                        f"{table_name} nested"
                    )


                    row = nested_rows[
                        nested_table_name
                    ][
                        str(index)
                    ]


                    row[
                        "identifier"
                    ] = (
                        f"{assignment_id}"
                        f"#{index}"
                    )


                    row[
                        "assignment_id"
                    ] = assignment_id


                    row[
                        "nested_index"
                    ] = index


                    row[
                        key
                    ] = item


    # ========================================================
    # PROCESS ITEM
    # ========================================================

    def process_item(item):

        if not isinstance(
            item,
            dict
        ):

            return


        raw_key = item.get(
            "dataKey"
        )


        if not raw_key:

            return


        # ====================================================
        # DATAKEY + INDEX
        # ====================================================

        data_key, nested_index = (
            parse_data_key(
                raw_key
            )
        )


        # ====================================================
        # CARI BLOK
        # ====================================================

        block_name = field_mapping.get(
            data_key
        )


        if not block_name:

            return


        # ====================================================
        # ANSWER
        # ====================================================

        answer = clean_value(
            item.get(
                "answer"
            )
        )


        # ====================================================
        # DATAKEY #1 / #2 / #3
        # ====================================================

        if nested_index is not None:

            table_name = (
                f"{block_name} nested"
            )


            row = nested_rows[
                table_name
            ][
                str(nested_index)
            ]


            row[
                "identifier"
            ] = (
                f"{assignment_id}"
                f"#{nested_index}"
            )


            row[
                "assignment_id"
            ] = assignment_id


            row[
                "nested_index"
            ] = nested_index


            # -----------------------------------------------
            # Kalau answer adalah object/list,
            # pecah ke nested table
            # -----------------------------------------------

            if isinstance(
                answer,
                (dict, list)
            ):

                process_nested_object(
                    block_name,
                    data_key,
                    answer
                )

            else:

                add_value(
                    row,
                    data_key,
                    answer
                )


            return


        # ====================================================
        # ANSWER OBJECT / LIST
        # ====================================================

        if isinstance(
            answer,
            (dict, list)
        ):

            process_nested_object(
                block_name,
                data_key,
                answer
            )

            return


        # ====================================================
        # DATA NORMAL
        # ====================================================

        row = main_rows[
            block_name
        ]


        row[
            "assignment_id"
        ] = assignment_id


        add_value(
            row,
            data_key,
            answer
        )


    # ========================================================
    # PROCESS PREDEFINED DATA
    # ========================================================

    for item in predata:

        process_item(
            item
        )


    # ========================================================
    # PROCESS ANSWERS
    # ========================================================

    for item in answers:

        process_item(
            item
        )


    # ========================================================
    # RETURN
    # ========================================================

    return {

        "principal data":
            principal,

        "main":
            dict(
                main_rows
            ),

        "nested":
            {
                table: list(
                    rows.values()
                )
                for (
                    table,
                    rows
                ) in nested_rows.items()
            }
    }


# ============================================================
# PROSES BANYAK FILE
# ============================================================

def process_files(
    template_path=None,
    input_dir=None,
    output_file=None
):

    # --------------------------------------------------------
    # Default path
    # --------------------------------------------------------

    template_path = (
        Path(template_path)
        if template_path
        else Path(TEMPLATE_FILE)
    )


    input_dir = (
        Path(input_dir)
        if input_dir
        else INPUT_DIR
    )


    output_file = (
        Path(output_file)
        if output_file
        else Path(OUTPUT_FILE)
    )


    # ========================================================
    # TEMPLATE
    # ========================================================

    template = load_json(
        template_path
    )


    blocks = find_blocks(
        template
    )


    field_mapping = create_mapping(
        blocks
    )


    print()
    print("=" * 70)
    print("TEMPLATE")
    print("=" * 70)


    print(
        f"Blok type:1 : "
        f"{len(blocks)}"
    )


    for block in blocks:

        print(
            f"  {block['name']} "
            f"→ "
            f"{len(block['fields'])} dataKey"
        )


    # ========================================================
    # CARI FILE JSON
    # ========================================================

    files = sorted(
        input_dir.glob(
            "*.json"
        )
    )


    if not files:

        raise FileNotFoundError(
            f"Tidak ada JSON di "
            f"{input_dir}"
        )


    if len(files) > MAX_FILES:

        raise ValueError(
            f"Maksimal {MAX_FILES} "
            f"answer JSON. "
            f"Ditemukan {len(files)}."
        )


    print()
    print(
        f"File ditemukan: "
        f"{len(files)}"
    )


    # ========================================================
    # HASIL
    # ========================================================

    principal_rows = []

    main_tables = defaultdict(
        list
    )

    nested_tables = defaultdict(
        list
    )


    # ========================================================
    # PROCESS SEMUA FILE
    # ========================================================

    for number, file_path in enumerate(
        files,
        start=1
    ):

        print(
            f"[{number}/{len(files)}] "
            f"{file_path.name}"
        )


        try:

            result = process_file(
                file_path,
                field_mapping
            )


            principal_rows.append(
                result[
                    "principal data"
                ]
            )


            # -----------------------------------------------
            # TABLE NORMAL
            # -----------------------------------------------

            for (
                table,
                row
            ) in result[
                "main"
            ].items():

                main_tables[
                    table
                ].append(
                    row
                )


            # -----------------------------------------------
            # TABLE NESTED
            # -----------------------------------------------

            for (
                table,
                rows
            ) in result[
                "nested"
            ].items():

                nested_tables[
                    table
                ].extend(
                    rows
                )


        except Exception as e:

            print(
                f"  ERROR: {e}"
            )


    # ========================================================
    # OUTPUT
    # ========================================================

    output = {

        "principal data":
            principal_rows,

        "tables":
            dict(
                main_tables
            ),

        "nested":
            dict(
                nested_tables
            )
    }


    # ========================================================
    # SAVE
    # ========================================================

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=4
        )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("CLEANING BERHASIL")
    print("=" * 70)


    print(
        f"File diproses : "
        f"{len(files)}"
    )


    print(
        f"Blok          : "
        f"{len(blocks)}"
    )


    print(
        f"Principal     : "
        f"{len(principal_rows)} baris"
    )


    print(
        f"Table normal  : "
        f"{len(main_tables)}"
    )


    print(
        f"Table nested  : "
        f"{len(nested_tables)}"
    )


    print(
        f"Output        : "
        f"{output_file}"
    )


    print("=" * 70)


    return output


# ============================================================
# MAIN
# ============================================================

def main():

    process_files()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()