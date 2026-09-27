"""意味パーツ単位の一次形状ゲートを検査する共通処理。"""

from __future__ import annotations

import json
from pathlib import Path


SCHEMA = "bpy_part_primary_form_gate/v1"
VIEW_METRICS = (
    "aspect_score",
    "silhouette_iou",
    "contour_f1",
    "landmark_score",
)
PART_METRICS = (
    "dimension_score",
    "depth_score",
    "connection_score",
)
LATER_STAGES = {
    "G3_SECONDARY_FORM",
    "G4_TOPOLOGY",
    "G5_MATERIAL",
    "G6_MICRODETAIL",
    "G7_DELIVERY",
}


def _score(value, location, errors):
    """Input: 任意値。Output: 0..1のfloat。範囲外はerrorsへ記録する。"""
    try:
        result = float(value)
    except (TypeError, ValueError):
        errors.append("%s must be a numeric score" % location)
        return 0.0
    if not 0.0 <= result <= 1.0:
        errors.append("%s must be between 0 and 1" % location)
    return result


def evaluate_primary_form_gate(data):
    """Input: ゲート契約dict。Output: 詳細な判定レポートdict。"""
    errors = []
    if data.get("schema") != SCHEMA:
        errors.append("unsupported schema")
    coarse_threshold = _score(
        data.get("coarse_threshold"), "coarse_threshold", errors
    )
    final_threshold = _score(
        data.get("final_threshold"), "final_threshold", errors
    )
    if final_threshold < 0.99:
        errors.append("final_threshold must remain at least 0.99")
    if coarse_threshold >= final_threshold:
        errors.append("coarse_threshold must be below final_threshold")

    parts = data.get("parts")
    if not isinstance(parts, list) or not parts:
        errors.append("parts must not be empty")
        parts = []

    seen = set()
    part_reports = {}
    for part_index, part in enumerate(parts):
        prefix = "parts[%d]" % part_index
        if not isinstance(part, dict):
            errors.append("%s must be an object" % prefix)
            continue
        part_id = part.get("id")
        if not isinstance(part_id, str) or not part_id.strip():
            errors.append("%s.id is required" % prefix)
            continue
        if part_id in seen:
            errors.append("duplicate part id: %s" % part_id)
            continue
        seen.add(part_id)

        required_views = part.get("required_views")
        if not isinstance(required_views, list) or not required_views:
            errors.append("%s.required_views must not be empty" % prefix)
            required_views = []
        views = part.get("views")
        if not isinstance(views, dict):
            errors.append("%s.views must be an object" % prefix)
            views = {}
        required_view_metrics = part.get("required_view_metrics", VIEW_METRICS)
        if (
            not isinstance(required_view_metrics, list)
            or not required_view_metrics
            or any(metric not in VIEW_METRICS for metric in required_view_metrics)
        ):
            errors.append(
                "%s.required_view_metrics must be a non-empty subset of %s"
                % (part_id, ", ".join(VIEW_METRICS))
            )
            required_view_metrics = VIEW_METRICS

        cells = []
        for view_name in required_views:
            view = views.get(view_name)
            if not isinstance(view, dict):
                errors.append("%s missing required view %s" % (part_id, view_name))
                continue
            for metric_name in required_view_metrics:
                value = _score(
                    view.get(metric_name),
                    "%s.views.%s.%s" % (part_id, view_name, metric_name),
                    errors,
                )
                cells.append({
                    "scope": "view",
                    "view": view_name,
                    "metric": metric_name,
                    "score": value,
                    "coarse_pass": value >= coarse_threshold,
                    "final_pass": value >= final_threshold,
                })

        part_metrics = part.get("part_metrics")
        if not isinstance(part_metrics, dict):
            errors.append("%s.part_metrics must be an object" % part_id)
            part_metrics = {}
        for metric_name in PART_METRICS:
            value = _score(
                part_metrics.get(metric_name),
                "%s.part_metrics.%s" % (part_id, metric_name),
                errors,
            )
            cells.append({
                "scope": "part",
                "view": None,
                "metric": metric_name,
                "score": value,
                "coarse_pass": value >= coarse_threshold,
                "final_pass": value >= final_threshold,
            })

        minimum = min((cell["score"] for cell in cells), default=0.0)
        part_reports[part_id] = {
            "name": part.get("name", part_id),
            "representation": part.get("representation"),
            "required_view_metrics": list(required_view_metrics),
            "minimum_score": minimum,
            "coarse_pass": bool(cells) and all(cell["coarse_pass"] for cell in cells),
            "final_pass": bool(cells) and all(cell["final_pass"] for cell in cells),
            "cells": cells,
        }

    coarse_pass = bool(part_reports) and all(
        report["coarse_pass"] for report in part_reports.values()
    )
    requested_stage = data.get("requested_stage", "G2_PRIMARY_FORM")
    stage_allowed = requested_stage not in LATER_STAGES or coarse_pass
    if not stage_allowed:
        errors.append(
            "%s is forbidden while one or more primary-form cells fail"
            % requested_stage
        )
    return {
        "schema": "bpy_part_primary_form_gate_report/v1",
        "asset": data.get("asset"),
        "requested_stage": requested_stage,
        "coarse_threshold": coarse_threshold,
        "final_threshold": final_threshold,
        "parts": part_reports,
        "minimum_score": min(
            (report["minimum_score"] for report in part_reports.values()),
            default=0.0,
        ),
        "coarse_pass": coarse_pass,
        "final_pass": bool(part_reports) and all(
            report["final_pass"] for report in part_reports.values()
        ),
        "stage_allowed": stage_allowed,
        "errors": errors,
        "valid": not errors,
    }


def evaluate_primary_form_gate_file(path):
    """Input: JSONパス。Output: evaluate_primary_form_gateのレポート。"""
    source = Path(path)
    return evaluate_primary_form_gate(json.loads(source.read_text(encoding="utf-8")))
