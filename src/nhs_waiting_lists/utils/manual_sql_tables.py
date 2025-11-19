from nhs_waiting_lists.constants import rtt_base_columns, numeric_cols


def create_rttwtd_table(conn, table_name):
    # Create the table with composite primary key
    create_sql = f"""
        CREATE TABLE IF NOT EXISTS `{table_name}` (
            {', '.join(rtt_base_columns)}, {', '.join([f"{col} INTEGER" for col in numeric_cols])},
            PRIMARY KEY (period,provider_org_code,rtt_part_type,treatment_function_code)
        )
    """
    # print(create_sql)
    cursor = conn.cursor()
    cursor.execute(create_sql)


def create_outpatient_activity_table(conn) -> None:
    """Create the metrics table with synthetic columns."""
    cursor = conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS outpatients_activity
                   (
                       -- keys
                       reporting_period  TEXT    NOT NULL,
                       geography_level   TEXT    NOT NULL,
                       organisation_code TEXT    NOT NULL,
                       measure_type      TEXT    NOT NULL,
                       measure           TEXT    NOT NULL,
                       -- Core metrics. can be masked '*' for 0-20 range
                       measure_value     REAL,

                       PRIMARY KEY (
                                    reporting_period,
                                    geography_level,
                                    organisation_code,
                                    measure_type,
                                    measure
                           )
                   ) STRICT;
                   """)
