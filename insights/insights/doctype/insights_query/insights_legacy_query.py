# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from copy import deepcopy
from json import dumps

import frappe
import pandas as pd
from frappe.utils.data import cstr

from insights.api import fetch_column_values, get_tables

from ..insights_data_source.sources.query_store import sync_query_store
from .utils import InsightsTable, get_columns_with_inferred_types

DEFAULT_FILTERS = dumps(
    {
        "type": "LogicalExpression",
        "operator": "&&",
        "level": 1,
        "position": 1,
        "conditions": [],
    },
    indent=2,
)


class InsightsLegacyQueryClient:
    @frappe.whitelist()
    def add_table(self, table):
        new_table = {
            "label": table.get("label"),
            "table": table.get("table"),
        }
        self.append("tables", new_table)
        self.save()

    @frappe.whitelist()
    def update_table(self, table):
        for row in self.tables:
            if row.get("name") != table.get("name"):
                continue

            if table.get("join"):
                row.join = dumps(
                    table.get("join"),
                    default=cstr,
                    indent=2,
                )
            else:
                row.join = ""

            self.save()
            return

    @frappe.whitelist()
    def remove_table(self, table):
        for row in self.tables:
            if row.get("name") == table.get("name"):
                self.remove(row)
                break

        self.save()

    @frappe.whitelist()
    def add_column(self, column):
        new_column = {
            "type": column.get("type"),
            "label": column.get("label"),
            "table": column.get("table"),
            "column": column.get("column"),
            "table_label": column.get("table_label"),
            "aggregation": column.get("aggregation"),
            "is_expression": column.get("is_expression"),
            "expression": dumps(column.get("expression"), indent=2),
            "format_option": dumps(column.get("format_option"), indent=2),
        }
        self.append("columns", new_column)
        self.save()

    @frappe.whitelist()
    def move_column(self, from_index, to_index):
        self.columns.insert(to_index, self.columns.pop(from_index))
        for row in self.columns:
            row.idx = self.columns.index(row) + 1
        self.save()

    @frappe.whitelist()
    def update_column(self, column):
        for row in self.columns:
            if row.get("name") == column.get("name"):
                row.type = column.get("type")
                row.label = column.get("label")
                row.table = column.get("table")
                row.column = column.get("column")
                row.order_by = column.get("order_by")
                row.aggregation = column.get("aggregation")
                row.table_label = column.get("table_label")
                row.aggregation_condition = column.get("aggregation_condition")
                format_option = column.get("format_option")
                if format_option:
                    # check if format option is an object
                    row.format_option = (
                        dumps(format_option, indent=2)
                        if isinstance(format_option, dict)
                        else format_option
                    )
                expression = column.get("expression")
                if expression:
                    # check if expression is an object
                    row.expression = (
                        dumps(expression, indent=2)
                        if isinstance(expression, dict)
                        else expression
                    )
                break

        self.save()

    @frappe.whitelist()
    def remove_column(self, column):
        for row in self.columns:
            if row.get("name") == column.get("name"):
                self.remove(row)
                break

        self.save()

    @frappe.whitelist()
    def update_filters(self, filters):
        sanitized_conditions = self.sanitize_conditions(filters.get("conditions"))
        filters["conditions"] = sanitized_conditions or []
        self.filters = dumps(filters, indent=2, default=cstr)
        self.save()

    def sanitize_conditions(self, conditions):
        if not conditions:
            return

        _conditions = deepcopy(conditions)

        for idx, condition in enumerate(_conditions):
            if "conditions" not in condition:
                # TODO: validate if condition is valid
                continue

            sanitized_conditions = self.sanitize_conditions(condition.get("conditions"))
            if sanitized_conditions:
                conditions[idx]["conditions"] = sanitized_conditions
            else:
                # remove the condition if it has zero conditions
                conditions.remove(condition)

        return conditions

    @frappe.whitelist()
    def fetch_tables(self):
        with_query_tables = frappe.db.get_single_value(
            "Insights Settings", "allow_subquery"
        )
        return get_tables(self.data_source, with_query_tables)

    @frappe.whitelist()
    def fetch_columns(self):
        return self.variant_controller.get_tables_columns()

    @frappe.whitelist()
    def fetch_column_values(self, column, search_text=None):
        return fetch_column_values(
            column.get("data_source") or self.data_source,
            column.get("table"),
            column.get("column"),
            search_text,
        )

    @frappe.whitelist()
    def fetch_join_options(self, left_table, right_table):
        left_doc = frappe.get_cached_doc(
            "Insights Table",
            {
                "table": left_table,
                "data_source": self.data_source,
            },
        )
        right_doc = frappe.get_cached_doc(
            "Insights Table",
            {
                "table": right_table,
                "data_source": self.data_source,
            },
        )

        links = []
        for link in left_doc.table_links:
            if link.foreign_table == right_table:
                links.append(
                    frappe._dict(
                        {
                            "left": link.primary_key,
                            "right": link.foreign_key,
                        }
                    )
                )

        return {
            "left_columns": left_doc.get_columns(),
            "right_columns": right_doc.get_columns(),
            "saved_links": links,
        }


class InsightsLegacyQueryValidation:
    def validate(self):
        self.validate_tables()
        self.validate_limit()
        self.validate_filters()
        self.validate_columns()

    def validate_tables(self):
        tables = [row.table for row in self.doc.tables]
        tables = frappe.get_all(
            "Insights Table",
            filters={"name": ("in", tables)},
            fields=["table", "data_source", "hidden"],
        )
        for table in tables:
            if table.hidden:
                frappe.throw(f"Table {table.table} is hidden. You cannot query it")
            if table.data_source != self.doc.data_source:
                frappe.throw(f"Table {table.table} is not in the same data source")

    def validate_limit(self):
        if self.doc.limit and self.doc.limit < 1:
            frappe.throw("Limit must be greater than 0")

    def validate_filters(self):
        if not self.doc.filters:
            self.filters = DEFAULT_FILTERS

    def validate_columns(self):
        if frappe.flags.in_test:
            return
        # check if no duplicate labelled columns
        labels = []
        for row in self.doc.columns:
            if row.label and row.label in labels:
                frappe.throw(f"Duplicate Column {row.label}")
            labels.append(row.label)


class InsightsLegacyQueryController(InsightsLegacyQueryValidation):
    def __init__(self, doc):
        self.doc = doc

    def after_reset(self):
        self.doc.filters = DEFAULT_FILTERS

    def get_sql(self):
        return self.doc._data_source.build_query(self.doc, with_cte=True)

    def get_columns(self):
        return self.get_columns_from_results(self.doc.retrieve_results())

    def get_columns_from_results(self, results):
        if not results:
            return []

        query_columns = self.doc.columns
        inferred_column_types = get_columns_with_inferred_types(results)
        if not query_columns:
            return inferred_column_types

        def get_inferred_column_type(result_column):
            for ic in inferred_column_types:
                if ic.get("label") == result_column.get("label"):
                    return ic.get("type")
            return "String"

        def add_format_options(result_column):
            result_column["format_options"] = {}
            result_column["type"] = get_inferred_column_type(result_column)
            for qc in query_columns:
                label_matches = qc.get("label") == result_column.get("label")
                column_matches = qc.get("column") == result_column.get("label")
                if not label_matches and not column_matches:
                    continue
                result_column["format_options"] = qc.get("format_option")
                result_column["type"] = qc.get("type")
                break
            return frappe._dict(result_column)

        result_columns = results[0]
        return [add_format_options(rc) for rc in result_columns]

    def get_tables_columns(self):
        columns = []
        selected_tables = self.get_selected_tables()
        for table in selected_tables:
            table_doc = InsightsTable.get_doc(
                data_source=self.doc.data_source,
                table=table.table,
            )
            table_columns = table_doc.get_columns()
            columns += [
                frappe._dict(
                    {
                        "data_source": self.doc.data_source,
                        "table_label": table.get("label"),
                        "table": table.get("table"),
                        "column": c.get("column"),
                        "label": c.get("label"),
                        "type": c.get("type"),
                    }
                )
                for c in table_columns
            ]
        return columns

    def get_selected_tables(self):
        join_tables = []
        for table in self.doc.tables:
            if table.join:
                join = frappe.parse_json(table.join)
                join_tables.append(
                    frappe._dict(
                        table=join.get("with").get("value"),
                        label=join.get("with").get("label"),
                    )
                )

        return self.doc.tables + join_tables

    def before_fetch(self):
        if self.doc.data_source != "Query Store":
            return
        sub_stored_queries = [
            t.table for t in self.doc.tables if t.table != self.doc.name
        ]
        sync_query_store(sub_stored_queries, force=True)

    def after_fetch_results(self, results):
        if self.has_cumulative_columns():
            results = self.apply_cumulative_sum(results)
        return results

    def has_cumulative_columns(self):
        return any(
            col.aggregation and "Cumulative" in col.aggregation
            for col in self.doc.columns
        )

    def apply_cumulative_sum(self, results):
        column_names = [d["label"] for d in results[0]]
        results_df = pd.DataFrame(results[1:], columns=column_names)

        for column in self.doc.columns:
            if "Cumulative" in column.aggregation:
                results_df[column.label] = results_df[column.label].cumsum()

        return [results[0]] + results_df.values.tolist()
