#!/usr/bin/env python3
"""Build the IYPT 2027 runnable-simulation archive from the v3 package contract.

The archive deliberately has two different outcomes:

* ten closed cases receive a dependency-free, deterministic synthetic
  implementation plus a native route adapter for the selected external solver;
* Amendment 05 adds provisional synthetic implementations for 05, 07, 11 and
  16 while preserving their model_selected_not_closed scientific status;
* 03, 13 and 14 remain justified scientific stops.

The synthetic path is software evidence only.  It never upgrades an external
solver to executed, numerically verified, or experimentally compared.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "deliverables" / "iypt-2027-consolidated"
PLUGIN = ROOT / "pt-research-plugin"
GENERIC_GENERATOR = PLUGIN / "tools" / "simulation-package" / "generate_package.py"
PACKAGE_REVISION = "iypt-2027-amendment-2026-08-07"
IMPLEMENTED = {
    "01-pinhole-sunglasses",
    "02-disc-spectrometer",
    "04-singing-capacitor",
    "06-seeing-sound",
    "08-upward-driven-disc",
    "09-photographic-bokeh",
    "10-air-vortex",
    "12-dotted-line-trick",
    "15-cold-drink",
    "17-falling-book-cover",
}
PROVISIONAL = {
    "05-y-shaped-pendulum",
    "07-sinking-funnel",
    "11-sound-isolation",
    "16-magnetic-carousel",
}
HOLDS: set[str] = set()
STOPS = {"03-snail-ball", "13-vortex-pendulum", "14-non-newtonian-worms"}


def _write(path: Path, value: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | 0o111)


def _write_json(path: Path, value: Any) -> None:
    _write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _import_generic_generator() -> Any:
    spec = importlib.util.spec_from_file_location("generic_package_generator", GENERIC_GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERIC_GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _case_inputs() -> dict[str, dict[str, Any]]:
    """Synthetic inputs are small, finite and intentionally labelled."""
    return {
        "01-pinhole-sunglasses": {
            "controls": {"wavelength_m": 5.5e-7, "f_e_m": 0.017, "delta_p_m_inv": 2.0, "pinhole_diameter_m": 3.0e-4, "pinhole_pitch_m": 1.2e-3, "pinhole_count": 25, "grid_points": 24},
            "material_properties": {},
            "geometry": {"pupil_diameter_m": 4.0e-3, "field_of_view_m": 2.0e-2, "spectacle_to_pupil_distance_m": 1.2e-2},
            "initial_conditions": {"gaze_angle_rad": 0.0},
            "boundary_conditions": {"aperture_mask": "opaque film with circular holes"},
            "calibration_parameters": {"throughput_factor": 0.8},
        },
        "02-disc-spectrometer": {
            "controls": {"wavelength_m": 5.5e-7, "order_m": 1, "incidence_alpha_rad": 0.1, "source_width_m": 2.0e-4, "grid_points": 24},
            "material_properties": {},
            "geometry": {"grating_pitch_m": 1.0e-6, "focal_length_m": 0.1, "illuminated_lines": 5000},
            "initial_conditions": {"phase_offset_rad": 0.0},
            "boundary_conditions": {"spectral_window_m": 1.0e-7},
            "calibration_parameters": {"aberration_width_m": 3.0e-5, "detector_pixel_m": 1.0e-5},
        },
        "04-singing-capacitor": {
            "controls": {"drive_voltage_v": 20.0, "frequency_hz": 1000.0, "grid_points": 12},
            "material_properties": {"youngs_modulus_pa": 2.0e9, "density_kg_m3": 1200.0, "piezo_d33_m_v": 2.0e-10, "quadratic_q33_m2_v2": 2.0e-12},
            "geometry": {"length_m": 1.0e-2, "width_m": 4.0e-3, "thickness_m": 5.0e-4, "electrode_area_m2": 4.0e-5},
            "initial_conditions": {},
            "boundary_conditions": {"root": "clamped", "acoustic_boundary": "radiating"},
            "calibration_parameters": {"modal_mass_kg": 1.0e-5, "modal_stiffness_n_m": 100.0, "modal_damping_n_s_m": 1.0e-3, "radiation_impedance_pa_s_m": 2.0e3},
        },
        "06-seeing-sound": {
            "controls": {"drive_pressure_pa": 1.0, "frequency_hz": 800.0, "grid_points": 16},
            "material_properties": {"areal_density_kg_m2": 0.8},
            "geometry": {"mirror_radius_m": 0.05, "mirror_thickness_m": 1.0e-3, "optical_path_m": 1.5},
            "initial_conditions": {"displacement_m": 0.0, "velocity_m_s": 0.0},
            "boundary_conditions": {"edge_condition": "clamped circular edge", "pressure_profile": "uniform synthetic drive"},
            "calibration_parameters": {"tension_n_m": 20.0, "modal_damping_n_s_m": 0.08},
        },
        "08-upward-driven-disc": {
            "controls": {"forcing_amplitude": 0.2, "forcing_frequency_hz": 1.0, "duration_s": 2.0, "time_step_s": 0.01, "grid_points": 16},
            "material_properties": {"inertia_kg_m2": 1.0, "disc_mass_kg": 0.5},
            "geometry": {"disc_radius_m": 0.05},
            "initial_conditions": {"y0": 0.1, "z0": 0.05, "omega0": 0.0},
            "boundary_conditions": {"axis_support": "fixed vertical axis"},
            "calibration_parameters": {"gravity_m_s2": 9.81, "damping_gain": 0.1},
        },
        "09-photographic-bokeh": {
            "controls": {"wavelength_m": 5.5e-7, "grid_points": 24, "field_of_view_m": 2.0e-3},
            "material_properties": {},
            "geometry": {"pupil_diameter_m": 8.0e-3, "focal_length_m": 5.0e-2},
            "initial_conditions": {"defocus_m": 1.0e-3},
            "boundary_conditions": {"aperture_shape": "circular"},
            "calibration_parameters": {"sensor_pixel_m": 4.0e-6, "throughput_factor": 0.9},
        },
        "10-air-vortex": {
            "controls": {"stirrer_angular_rate_rad_s": 12.0, "slip_factor": 0.8, "grid_points": 20},
            "material_properties": {"density_kg_m3": 1.2, "kinematic_viscosity_m2_s": 1.5e-5, "gravity_m_s2": 9.81},
            "geometry": {"radius_m": 0.05, "liquid_height_m": 0.08, "stirrer_radius_m": 0.02},
            "initial_conditions": {"free_surface_level_m": 0.08},
            "boundary_conditions": {"free_surface": "atmospheric"},
            "calibration_parameters": {"critical_depth_m": 0.01},
        },
        "12-dotted-line-trick": {
            "controls": {"stage_speed_m_s": 0.02, "duration_s": 2.0, "time_step_s": 0.001},
            "material_properties": {"mass_kg": 0.01, "static_friction": 0.45, "kinetic_friction": 0.35, "normal_load_n": 0.8},
            "geometry": {"spring_stiffness_n_m": 40.0, "damping_n_s_m": 0.02, "contact_width_m": 1.0e-3},
            "initial_conditions": {"position_m": 0.0, "velocity_m_s": 0.0},
            "boundary_conditions": {"contact_mode": "stick-slip with measured normal load"},
            "calibration_parameters": {"reset_force_n": 0.05, "slip_duration_s": 0.03, "deposit_energy_threshold_j": 1.0e-4, "mark_visibility_factor": 1.0, "deposited_mass_per_event_kg": 2.0e-5},
        },
        "15-cold-drink": {
            "controls": {"duration_s": 600.0, "time_step_s": 1.0, "salt_fraction": 0.05, "alcohol_fraction": 0.02},
            "material_properties": {"drink_specific_heat_j_kg_k": 4000.0, "bath_specific_heat_j_kg_k": 3900.0, "ice_specific_heat_j_kg_k": 2100.0, "latent_heat_j_kg": 334000.0},
            "geometry": {"drink_mass_kg": 0.33, "area_m2": 0.03, "bath_mass_kg": 1.0, "ice_mass_kg": 0.5},
            "initial_conditions": {"drink_temperature_k": 298.15, "bath_temperature_k": 268.15, "environment_temperature_k": 295.15},
            "boundary_conditions": {"bath_mixing": "well mixed", "phase_change": "ice melts at freezing curve"},
            "calibration_parameters": {"overall_heat_transfer_w_m2_k": 25.0, "environment_heat_leak_w": 1.0, "freezing_base_k": 273.15, "freezing_salt_shift_k": 18.0, "freezing_alcohol_shift_k": 8.0},
        },
        "17-falling-book-cover": {
            "controls": {"motor_torque_nm": 0.05, "duration_s": 1.0, "time_step_s": 0.001},
            "material_properties": {"book_mass_kg": 0.5, "book_inertia_kg_m2": 0.02, "air_density_kg_m3": 1.2, "air_viscosity_pa_s": 1.8e-5},
            "geometry": {"hinge_radius_m": 0.12, "book_area_m2": 0.08, "initial_gap_m": 4.0e-3, "edge_length_m": 0.3},
            "initial_conditions": {"theta0_rad": 0.2, "omega0_rad_s": 0.0},
            "boundary_conditions": {"hinge": "fixed rotational axis", "squeeze_cutoff_m": 5.0e-4},
            "calibration_parameters": {"hinge_damping_n_m_s": 0.01, "drag_coefficient": 1.1, "squeeze_coefficient": 2.0e-5},
        },
        "05-y-shaped-pendulum": {
            "controls": {"duration_s": 3.0, "time_step_s": 0.002, "gravity_m_s2": 9.81},
            "material_properties": {"bob_mass_kg": 0.08, "junction_mass_kg": 0.003},
            "geometry": {"support_half_spacing_m": 0.10, "support_height_m": 0.0, "junction_rest_z_m": -0.22, "bob_rest_z_m": -0.68, "upper_left_length_m": 0.23, "upper_right_length_m": 0.23, "lower_length_m": 0.46},
            "initial_conditions": {"bob_x0_m": 0.018, "bob_y0_m": 0.010, "bob_vx0_m_s": 0.0, "bob_vy0_m_s": 0.0, "junction_x0_m": 0.0, "junction_y0_m": 0.0, "junction_vx0_m_s": 0.0, "junction_vy0_m_s": 0.0},
            "boundary_conditions": {"topology": "two upper strings plus lower string", "strings_unilateral": True},
            "calibration_parameters": {"stiffness_x_n_m": 0.42, "stiffness_y_n_m": 0.58, "cross_coupling_n_m": 0.06, "damping_x_kg_s": 0.004, "damping_y_kg_s": 0.005, "constraint_stiffness_n_m": 5.0, "constraint_damping_kg_s": 0.08},
        },
        "07-sinking-funnel": {
            "controls": {"duration_s": 2.0, "time_step_s": 0.002, "gravity_m_s2": 9.81},
            "material_properties": {"funnel_mass_kg": 0.08, "water_density_kg_m3": 998.0, "water_viscosity_pa_s": 0.001},
            "geometry": {"displaced_volume_m3": 8.0e-5, "internal_area_m2": 2.5e-4, "throat_area_m2": 1.0e-4, "water_depth_m": 0.25, "funnel_length_m": 0.12},
            "initial_conditions": {"z0_m": 0.0, "dz0_m_s": 0.0, "eta0_m": 0.0, "flow0_m3_s": 0.0, "pitch0_rad": 0.0, "pitch_rate0_rad_s": 0.0},
            "boundary_conditions": {"topology": "open", "free_surface": "atmospheric", "surface_boundary": "VOF"},
            "calibration_parameters": {"added_mass_kg": 0.03, "heave_damping_n_s_m": 0.12, "heave_stiffness_n_m": 4.0, "hydraulic_inertance_pa_s2_m3": 1000.0, "hydraulic_resistance_pa_s2_m6": 1.0e6, "pitch_inertia_kg_m2": 2.0e-4, "pitch_damping_n_m_s": 4.0e-4, "pitch_stiffness_n_m": 0.003, "flow_coupling_n_s_m3": 0.01, "pitch_coupling_n_m_s": 0.02, "tip_limit_rad": 0.6},
        },
        "11-sound-isolation": {
            "controls": {"source_pressure_pa": 1.0, "frequency_hz": 800.0},
            "material_properties": {"air_density_kg_m3": 1.2, "sound_speed_m_s": 343.0, "kinematic_viscosity_m2_s": 1.5e-5, "thermal_diffusivity_m2_s": 2.2e-5, "gamma": 1.4},
            "geometry": {"slit_width_m": 0.001, "slit_height_m": 0.05, "slit_thickness_m": 0.04, "source_area_m2": 1.0, "receiver_area_m2": 1.0},
            "initial_conditions": {"pressure_phase_rad": 0.0},
            "boundary_conditions": {"partition_topology": "door slit", "flanking_path": "excluded"},
            "calibration_parameters": {"end_correction_factor": 1.7, "base_resistance_pa_s_m3": 1000.0, "thermoviscous_factor": 1.0, "flanking_power_fraction": 0.0},
        },
        "16-magnetic-carousel": {
            "controls": {"drive_rate_rad_s": 12.0, "duration_s": 4.0, "time_step_s": 0.002, "array_count": 8},
            "material_properties": {"ball_mass_kg": 0.02, "ball_inertia_kg_m2": 3.2e-6, "static_friction": 0.25, "kinetic_friction": 0.20},
            "geometry": {"array_radius_m": 0.08, "ball_radius_m": 0.006, "plate_gap_m": 0.012},
            "initial_conditions": {"carousel_angle_rad": 0.0, "ball_angle_rad": 0.0, "ball_rate_rad_s": 0.0, "ball_spin_rad_s": 0.0},
            "boundary_conditions": {"contact_mode": "rolling/sliding", "plate_nonmagnetic": True},
            "calibration_parameters": {"magnetic_potential_j": 8.0e-5, "radial_resisting_torque_nm": 1.0e-5, "sliding_speed_m_s": 0.01, "magnetic_harmonic_fraction": 0.15},
        },
    }


UNIT_MAP: dict[str, dict[str, str]] = {
    "01-pinhole-sunglasses": {"wavelength_m": "m", "f_e_m": "m", "delta_p_m_inv": "1/m", "pinhole_diameter_m": "m", "pinhole_pitch_m": "m", "pinhole_count": "1", "grid_points": "1", "pupil_diameter_m": "m", "field_of_view_m": "m", "spectacle_to_pupil_distance_m": "m", "gaze_angle_rad": "rad", "throughput_factor": "1"},
    "02-disc-spectrometer": {"wavelength_m": "m", "order_m": "1", "incidence_alpha_rad": "rad", "source_width_m": "m", "grid_points": "1", "grating_pitch_m": "m", "focal_length_m": "m", "illuminated_lines": "1", "phase_offset_rad": "rad", "spectral_window_m": "m", "aberration_width_m": "m", "detector_pixel_m": "m"},
    "04-singing-capacitor": {"drive_voltage_v": "V", "frequency_hz": "Hz", "grid_points": "1", "youngs_modulus_pa": "Pa", "density_kg_m3": "kg/m3", "piezo_d33_m_v": "m/V", "quadratic_q33_m2_v2": "m2/V2", "length_m": "m", "width_m": "m", "thickness_m": "m", "electrode_area_m2": "m2", "modal_mass_kg": "kg", "modal_stiffness_n_m": "N/m", "modal_damping_n_s_m": "N s/m", "radiation_impedance_pa_s_m": "Pa s/m"},
    "06-seeing-sound": {"drive_pressure_pa": "Pa", "frequency_hz": "Hz", "grid_points": "1", "areal_density_kg_m2": "kg/m2", "mirror_radius_m": "m", "mirror_thickness_m": "m", "optical_path_m": "m", "displacement_m": "m", "velocity_m_s": "m/s", "tension_n_m": "N/m", "modal_damping_n_s_m": "N s/m"},
    "08-upward-driven-disc": {"forcing_amplitude": "1", "forcing_frequency_hz": "Hz", "duration_s": "s", "time_step_s": "s", "grid_points": "1", "inertia_kg_m2": "kg m2", "disc_mass_kg": "kg", "disc_radius_m": "m", "y0": "1", "z0": "1", "omega0": "1", "gravity_m_s2": "m/s2", "damping_gain": "1"},
    "09-photographic-bokeh": {"wavelength_m": "m", "grid_points": "1", "field_of_view_m": "m", "pupil_diameter_m": "m", "focal_length_m": "m", "defocus_m": "m", "sensor_pixel_m": "m", "throughput_factor": "1"},
    "10-air-vortex": {"stirrer_angular_rate_rad_s": "rad/s", "slip_factor": "1", "grid_points": "1", "density_kg_m3": "kg/m3", "kinematic_viscosity_m2_s": "m2/s", "gravity_m_s2": "m/s2", "radius_m": "m", "liquid_height_m": "m", "stirrer_radius_m": "m", "free_surface_level_m": "m", "critical_depth_m": "m"},
    "12-dotted-line-trick": {"stage_speed_m_s": "m/s", "duration_s": "s", "time_step_s": "s", "mass_kg": "kg", "static_friction": "1", "kinetic_friction": "1", "normal_load_n": "N", "spring_stiffness_n_m": "N/m", "damping_n_s_m": "N s/m", "contact_width_m": "m", "position_m": "m", "velocity_m_s": "m/s", "reset_force_n": "N", "slip_duration_s": "s", "deposit_energy_threshold_j": "J", "mark_visibility_factor": "1", "deposited_mass_per_event_kg": "kg"},
    "15-cold-drink": {"duration_s": "s", "time_step_s": "s", "salt_fraction": "1", "alcohol_fraction": "1", "drink_specific_heat_j_kg_k": "J/(kg K)", "bath_specific_heat_j_kg_k": "J/(kg K)", "ice_specific_heat_j_kg_k": "J/(kg K)", "latent_heat_j_kg": "J/kg", "drink_mass_kg": "kg", "area_m2": "m2", "bath_mass_kg": "kg", "ice_mass_kg": "kg", "drink_temperature_k": "K", "bath_temperature_k": "K", "environment_temperature_k": "K", "overall_heat_transfer_w_m2_k": "W/(m2 K)", "environment_heat_leak_w": "W", "freezing_base_k": "K", "freezing_salt_shift_k": "K", "freezing_alcohol_shift_k": "K"},
    "17-falling-book-cover": {"motor_torque_nm": "N m", "duration_s": "s", "time_step_s": "s", "book_mass_kg": "kg", "book_inertia_kg_m2": "kg m2", "air_density_kg_m3": "kg/m3", "air_viscosity_pa_s": "Pa s", "hinge_radius_m": "m", "book_area_m2": "m2", "initial_gap_m": "m", "edge_length_m": "m", "theta0_rad": "rad", "omega0_rad_s": "rad/s", "squeeze_cutoff_m": "m", "hinge_damping_n_m_s": "N m s", "drag_coefficient": "1", "squeeze_coefficient": "N m s",},
    "05-y-shaped-pendulum": {"duration_s": "s", "time_step_s": "s", "gravity_m_s2": "m/s2", "bob_mass_kg": "kg", "junction_mass_kg": "kg", "support_half_spacing_m": "m", "support_height_m": "m", "junction_rest_z_m": "m", "bob_rest_z_m": "m", "upper_left_length_m": "m", "upper_right_length_m": "m", "lower_length_m": "m", "bob_x0_m": "m", "bob_y0_m": "m", "bob_vx0_m_s": "m/s", "bob_vy0_m_s": "m/s", "junction_x0_m": "m", "junction_y0_m": "m", "junction_vx0_m_s": "m/s", "junction_vy0_m_s": "m/s", "topology": "1", "strings_unilateral": "1", "stiffness_x_n_m": "N/m", "stiffness_y_n_m": "N/m", "cross_coupling_n_m": "N/m", "damping_x_kg_s": "kg/s", "damping_y_kg_s": "kg/s", "constraint_stiffness_n_m": "N/m", "constraint_damping_kg_s": "kg/s"},
    "07-sinking-funnel": {"duration_s": "s", "time_step_s": "s", "gravity_m_s2": "m/s2", "funnel_mass_kg": "kg", "water_density_kg_m3": "kg/m3", "water_viscosity_pa_s": "Pa s", "displaced_volume_m3": "m3", "internal_area_m2": "m2", "throat_area_m2": "m2", "water_depth_m": "m", "funnel_length_m": "m", "z0_m": "m", "dz0_m_s": "m/s", "eta0_m": "m", "flow0_m3_s": "m3/s", "pitch0_rad": "rad", "pitch_rate0_rad_s": "rad/s", "topology": "1", "free_surface": "1", "surface_boundary": "1", "added_mass_kg": "kg", "heave_damping_n_s_m": "N s/m", "heave_stiffness_n_m": "N/m", "hydraulic_inertance_pa_s2_m3": "Pa s2/m3", "hydraulic_resistance_pa_s2_m6": "Pa s2/m6", "pitch_inertia_kg_m2": "kg m2", "pitch_damping_n_m_s": "N m s", "pitch_stiffness_n_m": "N m/rad", "flow_coupling_n_s_m3": "N s/m3", "pitch_coupling_n_m_s": "N m s/m3", "tip_limit_rad": "rad"},
    "11-sound-isolation": {"source_pressure_pa": "Pa", "frequency_hz": "Hz", "air_density_kg_m3": "kg/m3", "sound_speed_m_s": "m/s", "kinematic_viscosity_m2_s": "m2/s", "thermal_diffusivity_m2_s": "m2/s", "gamma": "1", "slit_width_m": "m", "slit_height_m": "m", "slit_thickness_m": "m", "source_area_m2": "m2", "receiver_area_m2": "m2", "pressure_phase_rad": "rad", "end_correction_factor": "1", "base_resistance_pa_s_m3": "Pa s/m3", "thermoviscous_factor": "1", "flanking_power_fraction": "1"},
    "16-magnetic-carousel": {"drive_rate_rad_s": "rad/s", "duration_s": "s", "time_step_s": "s", "array_count": "1", "ball_mass_kg": "kg", "ball_inertia_kg_m2": "kg m2", "static_friction": "1", "kinetic_friction": "1", "array_radius_m": "m", "ball_radius_m": "m", "plate_gap_m": "m", "carousel_angle_rad": "rad", "ball_angle_rad": "rad", "ball_rate_rad_s": "rad/s", "ball_spin_rad_s": "rad/s", "contact_mode": "1", "plate_nonmagnetic": "1", "magnetic_potential_j": "J", "radial_resisting_torque_nm": "N m", "sliding_speed_m_s": "m/s", "magnetic_harmonic_fraction": "1"},
}


CASE_META: dict[str, dict[str, Any]] = {
    "01-pinhole-sunglasses": {"route": "fourier_optics", "solver": "HCIPy", "model_id": "c2", "wave": "Wave 1", "observable": "retinal point-spread width and modulation transfer, jointly with transmitted irradiance", "equations": ["propagation", "retinal", "optimum"], "native": "HCIPy pupil grid, wavelength and propagation adapter", "claim": "runnable_synthetic only; scalar/array synthetic optics benchmark passed; HCIPy and apparatus validation not claimed", "url": "https://docs.hcipy.org/"},
    "02-disc-spectrometer": {"route": "fourier_optics", "solver": "HCIPy", "model_id": "c2", "wave": "Wave 1", "observable": "spectral dispersion and instrument resolution", "equations": ["grating", "dispersion", "resolution"], "native": "HCIPy grating pupil/grid adapter", "claim": "runnable_synthetic only; grating-limit benchmark passed; HCIPy and apparatus validation not claimed", "url": "https://docs.hcipy.org/"},
    "04-singing-capacitor": {"route": "elmer_fem", "solver": "Elmer FEM", "model_id": "c2", "wave": "Wave 2", "observable": "frequency-dependent displacement and acoustic pressure response", "equations": ["strain", "force", "response"], "native": "Elmer FEM SIF, geometry and mesh-generation adapter", "claim": "runnable_synthetic only; piezo-modal benchmark passed; Elmer and apparatus validation not claimed", "url": "https://www.elmerfem.org/"},
    "06-seeing-sound": {"route": "elmer_fem", "solver": "Elmer FEM", "model_id": "c2", "wave": "Wave 2", "observable": "laser deflection produced by the sound-driven mirror", "equations": ["membrane", "modal", "laser"], "native": "Elmer FEM finite-mirror geometry and pressure-boundary adapter", "claim": "runnable_synthetic only; finite-mirror modal benchmark passed; Elmer and apparatus validation not claimed", "url": "https://www.elmerfem.org/"},
    "08-upward-driven-disc": {"route": "project_chrono", "solver": "Project Chrono", "model_id": "c1", "wave": "Wave 1", "observable": "disc state trajectory and angular response", "equations": ["kinematic", "angular", "dimensionless"], "native": "Project Chrono body/constraint/force/integrator adapter", "claim": "runnable_synthetic only; reduced dimensionless ODE benchmark passed; Chrono and apparatus validation not claimed", "url": "https://projectchrono.org/"},
    "09-photographic-bokeh": {"route": "fourier_optics", "solver": "HCIPy", "model_id": "c3", "wave": "Wave 1", "observable": "normalized point-spread profile and bokeh radius", "equations": ["pupil", "psf", "image"], "native": "HCIPy finite-pupil array and propagation adapter", "claim": "runnable_synthetic only; normalized PSF benchmark passed; HCIPy and apparatus validation not claimed", "url": "https://docs.hcipy.org/"},
    "10-air-vortex": {"route": "openfoam_continuum", "solver": "OpenFOAM", "model_id": "c3", "wave": "Wave 2", "observable": "vortex depth and rotation-onset threshold", "equations": ["radial", "surface", "onset"], "native": "OpenFOAM interFoam case with stirrer-to-fluid-rate mapping", "claim": "runnable_synthetic only; rotating-column benchmark passed; OpenFOAM and apparatus validation not claimed", "url": "https://openfoam.org/"},
    "12-dotted-line-trick": {"route": "python_ode", "solver": "Python/SciPy", "model_id": "c2", "wave": "Wave 2", "observable": "dot spacing, deposit mass, and stick/slip period", "equations": ["load", "slip", "spacing"], "native": "Python/SciPy event-driven ODE adapter with calibrated visibility gate", "claim": "runnable_synthetic only; stick-slip/visibility software benchmark passed; SciPy, material calibration and apparatus validation not claimed", "url": "https://docs.scipy.org/doc/scipy/"},
    "15-cold-drink": {"route": "python_ode", "solver": "Python/SciPy", "model_id": "c1", "wave": "Wave 1", "observable": "maximum cooling rate and lowest drink temperature", "equations": ["drink", "bath", "solution"], "native": "Python/SciPy enthalpy ODE with freezing-curve event handling", "claim": "runnable_synthetic only; enthalpy/phase-change benchmark passed; SciPy, ternary calibration and apparatus validation not claimed", "url": "https://docs.scipy.org/doc/scipy/"},
    "17-falling-book-cover": {"route": "project_chrono", "solver": "Project Chrono", "model_id": "c3", "wave": "Wave 2", "observable": "cover angle, angular rate, gap cutoff and energy diagnostics", "equations": ["rotation", "squeeze", "energy"], "native": "Project Chrono hinge/contact adapter with squeeze-film cutoff", "claim": "runnable_synthetic only; reduced hinge/squeeze benchmark passed; Chrono and apparatus validation not claimed", "url": "https://projectchrono.org/"},
    "05-y-shaped-pendulum": {"route": "project_chrono", "solver": "Project Chrono", "model_id": "c2", "wave": "Wave 3 amendment", "observable": "reduced modal frequencies, Lissajous closure time, and constrained Y-string trajectory diagnostics", "equations": ["matrix", "modes", "closure"], "native": "Project Chrono constrained Y-string dynamics adapter with explicit unilateral-string closure", "claim": "runnable_provisional only; reduced coupled-mode benchmark and constrained synthetic dynamics passed; string stiffness, slack transitions, Chrono and apparatus validation remain unestablished", "url": "https://projectchrono.org/", "scientific_readiness": "model_selected_not_closed", "implementation_status": "runnable_provisional", "provisional_model": True, "closure_blockers": ["Measure the complete Y-string geometry, branch tensions and slack/large-angle transitions before apparatus or predictive claims.", "Replace effective stiffness and penalty constraints with measured/derived constitutive closure before numerical verification."], "known_missing_physics": ["effective stiffness is an explicit calibration input", "penalty constraints approximate massless unilateral strings", "large-angle and slack transition dynamics are exploratory only"]},
    "07-sinking-funnel": {"route": "openfoam_continuum", "solver": "OpenFOAM", "model_id": "c3", "wave": "Wave 3 amendment", "observable": "heave trajectory, internal flow response, pitch envelope, and tipping stability margin", "equations": ["heave", "hydraulic", "stability"], "native": "OpenFOAM interFoam/free-surface case with documented open-funnel closures", "claim": "runnable_provisional only; reduced heave/hydraulic/pitch model and exploratory free-surface case generated; closure coefficients, OpenFOAM and apparatus validation remain unestablished", "url": "https://openfoam.org/", "scientific_readiness": "model_selected_not_closed", "implementation_status": "runnable_provisional", "provisional_model": True, "closure_blockers": ["Measure the funnel topology, entrained-air state and discharge/pressure closure before apparatus or predictive claims.", "Replace reduced inertance/resistance and pitch coupling with measured or derived values before CFD verification."], "known_missing_physics": ["VOF interface and entrained air are not solved by the synthetic path", "hydraulic resistance and inertance are calibration inputs", "wetting, turbulence and outlet boundary details remain unresolved"]},
    "11-sound-isolation": {"route": "elmer_fem", "solver": "Elmer FEM", "model_id": "c2", "wave": "Wave 3 amendment", "observable": "thermoviscous slit transmission loss and boundary-layer diagnostics", "equations": ["wave", "impedance", "tl"], "native": "Elmer FEM harmonic acoustic/thermoviscous slit adapter with reduced impedance benchmark", "claim": "runnable_provisional only; reduced aperture/acoustic and thermoviscous synthetic benchmarks passed; FEM, flanking paths and apparatus validation remain unestablished", "url": "https://www.elmerfem.org/", "scientific_readiness": "model_selected_not_closed", "implementation_status": "runnable_provisional", "provisional_model": True, "closure_blockers": ["Measure the complete slit/cavity/flanking topology and boundary losses before apparatus or predictive claims.", "Replace the lumped impedance and effective thermoviscous correction with measured or derived closure before FEM verification."], "known_missing_physics": ["flanking paths are explicitly excluded from the fixture", "end correction and resistance are calibration inputs", "full thermoviscous FEM boundary conditions remain to be specified"]},
    "16-magnetic-carousel": {"route": "project_chrono", "solver": "Project Chrono", "model_id": "c2", "wave": "Wave 3 amendment", "observable": "carousel/ball mean angular velocity, phase lag, slip fraction, and drift direction", "equations": ["magnetic", "motion", "contact"], "native": "Project Chrono contact dynamics driven by a measured/lookup magnetic force map", "claim": "runnable_provisional only; staged harmonic force-map and rolling/sliding contact workflow passed synthetically; magnetic map, hysteresis, Chrono and apparatus validation remain unestablished", "url": "https://projectchrono.org/", "scientific_readiness": "model_selected_not_closed", "implementation_status": "runnable_provisional", "provisional_model": True, "closure_blockers": ["Measure the 2D/3D magnetic force map, gap dependence and contact losses before apparatus or predictive claims.", "Escalate to a coupled magnetodynamics model only if the measured quasi-static map fails the registered falsifier."], "known_missing_physics": ["harmonic force map stands in for measured/FEM magnetics", "hysteresis and eddy-current loss are unresolved", "rolling/sliding transition and plate compliance are effective contact closures"]},
}


HOLD_INPUTS: dict[str, dict[str, Any]] = {
    "05-y-shaped-pendulum": {
        "measured_controls": {"mass_kg": {"unit": "kg", "provenance": "balance"}},
        "geometry": {"branch_length_x_m": {"unit": "m", "provenance": "geometry survey"}, "branch_length_y_m": {"unit": "m", "provenance": "geometry survey"}},
        "material_properties": {"damping_kg_s": {"unit": "kg/s", "provenance": "free-decay fit"}},
        "initial_conditions": {"amplitude_x_m": {"unit": "m", "provenance": "video"}, "amplitude_y_m": {"unit": "m", "provenance": "video"}, "phase_x_rad": {"unit": "rad", "provenance": "trajectory"}, "phase_y_rad": {"unit": "rad", "provenance": "trajectory"}},
        "boundary_conditions": {"support_topology": {"unit": "1", "provenance": "apparatus drawing"}},
        "fitted_calibration_values": {"stiffness_x_n_m": {"unit": "N/m", "provenance": "geometry/tension calibration"}, "stiffness_y_n_m": {"unit": "N/m", "provenance": "geometry/tension calibration"}},
    },
    "07-sinking-funnel": {
        "measured_controls": {"normal_load_n": {"unit": "N", "provenance": "balance"}},
        "geometry": {"displaced_volume_m3": {"unit": "m3", "provenance": "geometry"}, "inlet_area_m2": {"unit": "m2", "provenance": "geometry"}},
        "material_properties": {"water_density_kg_m3": {"unit": "kg/m3", "provenance": "densitometer"}},
        "initial_conditions": {"heave_m": {"unit": "m", "provenance": "video"}, "free_surface_level_m": {"unit": "m", "provenance": "video"}},
        "boundary_conditions": {"funnel_topology": {"unit": "1", "provenance": "apparatus audit"}, "pressure_drop_pa": {"unit": "Pa", "provenance": "pressure trace"}},
        "fitted_calibration_values": {"added_mass_kg": {"unit": "kg", "provenance": "decay/geometry"}, "hydraulic_inertance": {"unit": "Pa s2/m3", "provenance": "flow transient"}, "discharge_resistance": {"unit": "Pa s2/m6", "provenance": "flow calibration"}},
    },
    "11-sound-isolation": {
        "measured_controls": {"source_pressure_pa": {"unit": "Pa", "provenance": "microphone"}, "frequency_hz": {"unit": "Hz", "provenance": "source"}},
        "geometry": {"effective_length_m": {"unit": "m", "provenance": "geometry/end correction"}, "slit_area_m2": {"unit": "m2", "provenance": "geometry"}, "cavity_compliance_m3_pa": {"unit": "m3/Pa", "provenance": "cavity geometry"}},
        "material_properties": {"air_density_kg_m3": {"unit": "kg/m3", "provenance": "temperature/pressure"}, "sound_speed_m_s": {"unit": "m/s", "provenance": "temperature"}},
        "initial_conditions": {"volume_flow_m3_s": {"unit": "m3/s", "provenance": "particle-velocity method"}},
        "boundary_conditions": {"upstream_downstream": {"unit": "1", "provenance": "apparatus topology"}},
        "fitted_calibration_values": {"groove_impedance_pa_s_m3": {"unit": "Pa s/m3", "provenance": "impedance fit"}, "resistive_loss_pa_s_m3": {"unit": "Pa s/m3", "provenance": "flow/acoustic calibration"}},
    },
    "16-magnetic-carousel": {
        "measured_controls": {"drive_rate_rad_s": {"unit": "rad/s", "provenance": "encoder"}},
        "geometry": {"array_radius_m": {"unit": "m", "provenance": "caliper"}, "ball_radius_m": {"unit": "m", "provenance": "caliper"}, "array_count": {"unit": "1", "provenance": "array layout"}},
        "material_properties": {"ball_mass_kg": {"unit": "kg", "provenance": "balance"}, "ball_inertia_kg_m2": {"unit": "kg m2", "provenance": "geometry"}, "static_friction": {"unit": "1", "provenance": "contact test"}},
        "initial_conditions": {"carousel_angle_rad": {"unit": "rad", "provenance": "video"}, "ball_rate_rad_s": {"unit": "rad/s", "provenance": "mark tracking"}},
        "boundary_conditions": {"contact_mode": {"unit": "1", "provenance": "contact audit"}},
        "fitted_calibration_values": {"magnetic_potential_j": {"unit": "J", "provenance": "force-map integration/FEM"}, "radial_resisting_torque_nm": {"unit": "N m", "provenance": "coast-down"}, "sliding_speed_m_s": {"unit": "m/s", "provenance": "dynamics"}},
    },
}


def _model_source(case_id: str, observable: str, equation_ids: list[str]) -> str:
    header = textwrap.dedent(
        f"""
        \"\"\"Case-specific deterministic synthetic implementation for IYPT 2027.\"\"\"
        from __future__ import annotations

        import math
        from typing import Any, Callable

        CASE_ID = {case_id!r}
        OBSERVABLE = {observable!r}
        EQUATION_IDS = {equation_ids!r}
        UNITS = \"SI; see outputs for per-field units\"

        def value(data: dict[str, Any], category: str, name: str, default: float = 0.0) -> float:
            item = data.get(category, {{}}).get(name, default)
            if isinstance(item, dict):
                item = item.get(\"value\", default)
            return float(item)

        def positive(data: dict[str, Any], category: str, name: str, default: float = 1.0) -> float:
            result = value(data, category, name, default)
            if result <= 0.0 or not math.isfinite(result):
                raise ValueError(f\"{{category}}.{{name}} must be positive and finite\")
            return result

        def integer(data: dict[str, Any], category: str, name: str, default: int = 8) -> int:
            result = int(value(data, category, name, default))
            if result < 2:
                raise ValueError(f\"{{category}}.{{name}} must be at least 2\")
            return result

        def clamp(x: float, low: float, high: float) -> float:
            return min(high, max(low, x))

        def normalized_profile(count: int, fn: Callable[[int], float]) -> list[float]:
            raw = [max(0.0, float(fn(index))) for index in range(count)]
            total = sum(raw)
            if total <= 0.0 or not math.isfinite(total):
                raise ValueError(\"profile normalization failed\")
            return [item / total for item in raw]

        def rk4(state: list[float], dt: float, derivative: Callable[[list[float]], list[float]]) -> list[float]:
            k1 = derivative(state)
            s2 = [x + 0.5 * dt * y for x, y in zip(state, k1)]
            k2 = derivative(s2)
            s3 = [x + 0.5 * dt * y for x, y in zip(state, k2)]
            k3 = derivative(s3)
            s4 = [x + dt * y for x, y in zip(state, k3)]
            k4 = derivative(s4)
            return [x + dt * (a + 2.0 * b + 2.0 * c + d) / 6.0 for x, a, b, c, d in zip(state, k1, k2, k3, k4)]

        def result(value_out: float, outputs: dict[str, Any]) -> dict[str, Any]:
            if not math.isfinite(float(value_out)):
                raise ValueError(\"synthetic model produced a non-finite primary observable\")
            return {{\"case_id\": CASE_ID, \"observable\": OBSERVABLE, \"value\": float(value_out), \"unit\": UNITS, \"equation_id\": EQUATION_IDS[-1], \"equation_ids\": EQUATION_IDS, \"synthetic\": True, \"outputs\": outputs}}

        """
    ).lstrip()

    bodies: dict[str, str] = {
        "01-pinhole-sunglasses": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                wavelength = positive(data, "controls", "wavelength_m")
                focal = positive(data, "controls", "f_e_m")
                delta_p = abs(value(data, "controls", "delta_p_m_inv"))
                diameter = positive(data, "controls", "pinhole_diameter_m")
                pitch = positive(data, "controls", "pinhole_pitch_m")
                count = positive(data, "controls", "pinhole_count", 1.0)
                grid = integer(data, "controls", "grid_points")
                pupil = positive(data, "geometry", "pupil_diameter_m")
                field = positive(data, "geometry", "field_of_view_m")
                throughput = clamp(value(data, "calibration_parameters", "throughput_factor", 1.0), 0.0, 1.0)
                diffraction = 1.22 * wavelength * focal / diameter
                defocus = 0.5 * focal * delta_p * diameter
                rms = math.hypot(diffraction, defocus)
                optimum = 0.0 if delta_p == 0.0 else math.sqrt(2.44 * wavelength / delta_p)
                open_fraction = min(1.0, count * math.pi * (diameter / 2.0) ** 2 / (math.pi * (pupil / 2.0) ** 2))
                profile = normalized_profile(grid, lambda index: math.exp(-((index - (grid - 1) / 2.0) * field / grid) ** 2 / max(rms, 1.0e-12) ** 2))
                return result(rms, {"retinal_psf_rms_m": rms, "diffraction_radius_m": diffraction, "defocus_radius_m": defocus, "optimal_pinhole_diameter_m": optimum, "transmitted_irradiance_fraction": throughput * open_fraction, "radial_profile": profile, "sampling_points": grid, "pinhole_pitch_m": pitch})
            """
        ),
        "02-disc-spectrometer": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                wavelength = positive(data, "controls", "wavelength_m")
                order = positive(data, "controls", "order_m")
                alpha = value(data, "controls", "incidence_alpha_rad")
                source_width = positive(data, "controls", "source_width_m")
                grid = integer(data, "controls", "grid_points")
                pitch = positive(data, "geometry", "grating_pitch_m")
                focal = positive(data, "geometry", "focal_length_m")
                lines = positive(data, "geometry", "illuminated_lines")
                aberration = positive(data, "calibration_parameters", "aberration_width_m")
                detector = positive(data, "calibration_parameters", "detector_pixel_m")
                argument = clamp(order * wavelength / pitch - math.sin(alpha), -1.0, 1.0)
                beta = math.asin(argument)
                dispersion = focal * order / (pitch * max(math.cos(beta), 1.0e-12))
                resolution = math.sqrt((wavelength / (order * lines)) ** 2 + (source_width * pitch * math.cos(beta) / (focal * order)) ** 2 + aberration ** 2)
                profile = normalized_profile(grid, lambda index: math.exp(-0.5 * (((index - (grid - 1) / 2.0) * detector - dispersion * (wavelength - wavelength)) / max(resolution, detector)) ** 2))
                return result(dispersion, {"diffraction_angle_rad": beta, "dispersion_m_per_m": dispersion, "instrument_resolution_m": resolution, "line_profile": profile, "sampling_pixel_m": detector})
            """
        ),
        "04-singing-capacitor": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                voltage = value(data, "controls", "drive_voltage_v")
                frequency = positive(data, "controls", "frequency_hz")
                young = positive(data, "material_properties", "youngs_modulus_pa")
                d33 = value(data, "material_properties", "piezo_d33_m_v")
                q33 = value(data, "material_properties", "quadratic_q33_m2_v2")
                length = positive(data, "geometry", "length_m")
                width = positive(data, "geometry", "width_m")
                thickness = positive(data, "geometry", "thickness_m")
                area = positive(data, "geometry", "electrode_area_m2")
                mass = positive(data, "calibration_parameters", "modal_mass_kg")
                stiffness = positive(data, "calibration_parameters", "modal_stiffness_n_m")
                damping = positive(data, "calibration_parameters", "modal_damping_n_s_m")
                impedance = positive(data, "calibration_parameters", "radiation_impedance_pa_s_m")
                omega = 2.0 * math.pi * frequency
                field = voltage / thickness
                linear_strain = d33 * field
                quadratic_strain = q33 * field * field
                total_strain = linear_strain + quadratic_strain
                active_force = young * total_strain * area
                denominator = math.sqrt((stiffness - mass * omega * omega) ** 2 + (damping * omega) ** 2)
                displacement = active_force / max(denominator, 1.0e-18)
                pressure = impedance * omega * displacement
                return result(displacement, {"electric_field_v_m": field, "linear_strain": linear_strain, "quadratic_strain": quadratic_strain, "modal_force_n": active_force, "modal_displacement_m": displacement, "sound_pressure_pa": pressure, "beam_length_m": length, "beam_width_m": width})
            """
        ),
        "06-seeing-sound": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                pressure = value(data, "controls", "drive_pressure_pa")
                frequency = positive(data, "controls", "frequency_hz")
                areal_mass = positive(data, "material_properties", "areal_density_kg_m2")
                radius = positive(data, "geometry", "mirror_radius_m")
                thickness = positive(data, "geometry", "mirror_thickness_m")
                optical_path = positive(data, "geometry", "optical_path_m")
                tension = positive(data, "calibration_parameters", "tension_n_m")
                damping = positive(data, "calibration_parameters", "modal_damping_n_s_m")
                omega = 2.0 * math.pi * frequency
                modal_wavenumber = math.pi / radius
                stiffness = tension * modal_wavenumber ** 2
                modal_mass = areal_mass
                denominator = math.sqrt((stiffness - modal_mass * omega * omega) ** 2 + (damping * omega) ** 2)
                displacement = pressure / max(denominator, 1.0e-18)
                mirror_slope = displacement / radius
                laser_shift = 2.0 * optical_path * mirror_slope
                return result(laser_shift, {"finite_mirror_radius_m": radius, "modal_displacement_m": displacement, "mirror_slope_rad": mirror_slope, "laser_shift_m": laser_shift, "thickness_m": thickness})
            """
        ),
        "08-upward-driven-disc": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                forcing = value(data, "controls", "forcing_amplitude")
                forcing_frequency = positive(data, "controls", "forcing_frequency_hz")
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                y = value(data, "initial_conditions", "y0")
                z = value(data, "initial_conditions", "z0")
                omega = value(data, "initial_conditions", "omega0")
                damping = positive(data, "calibration_parameters", "damping_gain")
                steps = max(1, int(duration / dt))
                def derivative(state: list[float], time_s: float) -> list[float]:
                    local_omega, local_y, local_z = state
                    drive = forcing * math.sin(2.0 * math.pi * forcing_frequency * time_s)
                    return [local_y - damping * local_omega, local_omega * local_z, -local_omega * local_y + drive]
                time_s = 0.0
                for _ in range(steps):
                    omega, y, z = rk4([omega, y, z], dt, lambda state, t=time_s: derivative(state, t))
                    time_s += dt
                return result(y, {"final_y": y, "final_z": z, "final_omega": omega, "integrated_duration_s": time_s, "equation_form": "dimensionless reduced ODE"})
            """
        ),
        "09-photographic-bokeh": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                wavelength = positive(data, "controls", "wavelength_m")
                grid = integer(data, "controls", "grid_points")
                field = positive(data, "controls", "field_of_view_m")
                pupil = positive(data, "geometry", "pupil_diameter_m")
                focal = positive(data, "geometry", "focal_length_m")
                defocus = abs(value(data, "initial_conditions", "defocus_m"))
                pixel = positive(data, "calibration_parameters", "sensor_pixel_m")
                airy = 1.22 * wavelength * focal / pupil
                bokeh = pupil * defocus / max(2.0 * focal, 1.0e-18)
                sigma = math.hypot(airy, bokeh) / 2.355
                profile = normalized_profile(grid, lambda index: math.exp(-0.5 * (((index - (grid - 1) / 2.0) * field / grid) / max(sigma, pixel)) ** 2))
                return result(bokeh, {"airy_radius_m": airy, "bokeh_radius_m": bokeh, "psf_sigma_m": sigma, "psf_normalized_sum": sum(profile), "psf_profile": profile, "sampling_pixel_m": pixel})
            """
        ),
        "10-air-vortex": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                stirrer_rate = positive(data, "controls", "stirrer_angular_rate_rad_s")
                slip = clamp(value(data, "controls", "slip_factor", 1.0), 0.0, 1.0)
                density = positive(data, "material_properties", "density_kg_m3")
                gravity = positive(data, "material_properties", "gravity_m_s2")
                radius = positive(data, "geometry", "radius_m")
                height = positive(data, "geometry", "liquid_height_m")
                stirrer_radius = positive(data, "geometry", "stirrer_radius_m")
                critical_depth = positive(data, "calibration_parameters", "critical_depth_m")
                fluid_rate = stirrer_rate * slip * stirrer_radius / radius
                vortex_depth = min(height, fluid_rate * fluid_rate * radius * radius / (2.0 * gravity))
                onset = 2.0 * math.sqrt(gravity * critical_depth) / radius
                radial_pressure_gradient = density * fluid_rate * fluid_rate * radius
                return result(vortex_depth, {"stirrer_rate_rad_s": stirrer_rate, "fluid_angular_rate_rad_s": fluid_rate, "vortex_depth_m": vortex_depth, "onset_rate_rad_s": onset, "radial_pressure_gradient_pa_m": radial_pressure_gradient, "onset_reached": fluid_rate >= onset})
            """
        ),
        "12-dotted-line-trick": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                speed = positive(data, "controls", "stage_speed_m_s")
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                mass = positive(data, "material_properties", "mass_kg")
                mu_s = positive(data, "material_properties", "static_friction")
                mu_k = positive(data, "material_properties", "kinetic_friction")
                normal = positive(data, "material_properties", "normal_load_n")
                stiffness = positive(data, "geometry", "spring_stiffness_n_m")
                damping = positive(data, "geometry", "damping_n_s_m")
                reset = max(0.0, value(data, "calibration_parameters", "reset_force_n"))
                slip_time = positive(data, "calibration_parameters", "slip_duration_s")
                threshold_energy = positive(data, "calibration_parameters", "deposit_energy_threshold_j")
                visibility = clamp(value(data, "calibration_parameters", "mark_visibility_factor", 1.0), 0.0, 1.0)
                mass_per_event = positive(data, "calibration_parameters", "deposited_mass_per_event_kg")
                threshold_force = max(mu_s * normal - reset, 0.0)
                stick_time = threshold_force / max(stiffness * speed, 1.0e-18)
                spacing = threshold_force / stiffness + speed * slip_time
                stored_energy = 0.5 * threshold_force * threshold_force / stiffness
                visible_event = visibility * stored_energy >= threshold_energy
                period = stick_time + slip_time
                cycles = max(1, int(duration / max(period, dt)))
                # A short explicit stick/slip state trace is kept for an audit
                # hook; the registered spacing law remains the primary output.
                x = value(data, "initial_conditions", "position_m")
                v_contact = value(data, "initial_conditions", "velocity_m_s")
                dissipated = 0.0
                for step in range(max(1, int(duration / dt))):
                    t_now = step * dt
                    spring_force = stiffness * (speed * t_now - x)
                    if abs(spring_force) <= mu_s * normal and abs(v_contact) < 1.0e-8:
                        v_contact = 0.0
                    else:
                        sign = 1.0 if v_contact >= 0.0 else -1.0
                        acceleration = (-damping * v_contact - stiffness * (x - speed * t_now) - mu_k * normal * sign) / mass
                        v_contact += acceleration * dt
                        x += v_contact * dt
                        dissipated += (damping * v_contact * v_contact + mu_k * normal * abs(v_contact)) * dt
                return result(spacing, {"dot_spacing_m": spacing, "deposit_mass_kg": cycles * mass_per_event if visible_event else 0.0, "stick_slip_period_s": period, "stick_time_s": stick_time, "visible_event": visible_event, "visibility_rule": "mark_visibility_factor * stored spring energy >= deposit_energy_threshold_j", "stored_spring_energy_j": stored_energy, "dissipated_energy_j": dissipated, "cycle_count": cycles})
            """
        ),
        "15-cold-drink": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                salt = clamp(value(data, "controls", "salt_fraction"), 0.0, 1.0)
                alcohol = clamp(value(data, "controls", "alcohol_fraction"), 0.0, 1.0)
                cd = positive(data, "material_properties", "drink_specific_heat_j_kg_k")
                cb = positive(data, "material_properties", "bath_specific_heat_j_kg_k")
                ci = positive(data, "material_properties", "ice_specific_heat_j_kg_k")
                latent = positive(data, "material_properties", "latent_heat_j_kg")
                md = positive(data, "geometry", "drink_mass_kg")
                area = positive(data, "geometry", "area_m2")
                mb = positive(data, "geometry", "bath_mass_kg")
                ice = positive(data, "geometry", "ice_mass_kg")
                drink = value(data, "initial_conditions", "drink_temperature_k")
                bath = value(data, "initial_conditions", "bath_temperature_k")
                environment = value(data, "initial_conditions", "environment_temperature_k")
                conductance = positive(data, "calibration_parameters", "overall_heat_transfer_w_m2_k") * area
                heat_leak = value(data, "calibration_parameters", "environment_heat_leak_w")
                freezing = value(data, "calibration_parameters", "freezing_base_k") - value(data, "calibration_parameters", "freezing_salt_shift_k") * salt - value(data, "calibration_parameters", "freezing_alcohol_shift_k") * alcohol
                drink_capacity = md * cd
                bath_capacity = mb * cb + ice * ci
                samples = [drink]
                maximum_rate = 0.0
                ice_remaining = ice
                energy_residual = 0.0
                steps = max(1, int(duration / dt))
                for _ in range(steps):
                    heat_to_bath = conductance * (drink - bath)
                    old_drink, old_bath = drink, bath
                    drink += -heat_to_bath / drink_capacity * dt
                    available_to_melt = max(0.0, heat_to_bath + heat_leak)
                    if bath >= freezing and ice_remaining > 0.0:
                        melt = min(ice_remaining / dt, available_to_melt / latent)
                    else:
                        melt = 0.0
                    bath += (heat_to_bath - melt * latent + heat_leak) / max(bath_capacity, 1.0e-12) * dt
                    ice_remaining = max(0.0, ice_remaining - melt * dt)
                    maximum_rate = max(maximum_rate, (old_drink - drink) / dt)
                    energy_residual += drink_capacity * (drink - old_drink) + bath_capacity * (bath - old_bath) - (-heat_to_bath + heat_to_bath - melt * latent + heat_leak) * dt
                    samples.append(drink)
                minimum = min(samples)
                return result(maximum_rate, {"maximum_cooling_rate_k_s": maximum_rate, "lowest_drink_temperature_k": minimum, "final_drink_temperature_k": drink, "final_bath_temperature_k": bath, "freezing_curve_temperature_k": freezing, "remaining_ice_kg": ice_remaining, "energy_residual_j": energy_residual, "temperature_samples": samples[::max(1, len(samples) // 32)], "environment_temperature_k": environment})
            """
        ),
        "17-falling-book-cover": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                drive = value(data, "controls", "motor_torque_nm")
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                inertia = positive(data, "material_properties", "book_inertia_kg_m2")
                air_density = positive(data, "material_properties", "air_density_kg_m3")
                area = positive(data, "geometry", "book_area_m2")
                radius = positive(data, "geometry", "hinge_radius_m")
                gap0 = positive(data, "geometry", "initial_gap_m")
                edge = positive(data, "geometry", "edge_length_m")
                theta = value(data, "initial_conditions", "theta0_rad")
                omega = value(data, "initial_conditions", "omega0_rad_s")
                damping = positive(data, "calibration_parameters", "hinge_damping_n_m_s")
                drag = positive(data, "calibration_parameters", "drag_coefficient")
                squeeze = positive(data, "calibration_parameters", "squeeze_coefficient")
                cutoff = positive(data, "boundary_conditions", "squeeze_cutoff_m")
                min_gap = gap0
                dissipated = 0.0
                steps = max(1, int(duration / dt))
                for _ in range(steps):
                    gap = max(cutoff, gap0 - radius * abs(math.sin(theta)))
                    min_gap = min(min_gap, gap)
                    air_torque = 0.5 * air_density * drag * area * radius ** 3 * omega * abs(omega)
                    # The reduced squeeze-film coefficient is calibrated for
                    # the cutoff-regularized boundary; using the explicit
                    # cutoff avoids a singular torque in the synthetic path.
                    squeeze_torque = squeeze * omega / gap
                    acceleration = (drive - damping * omega - air_torque - squeeze_torque) / inertia
                    omega += acceleration * dt
                    theta += omega * dt
                    dissipated += (damping * omega * omega + abs(air_torque * omega) + abs(squeeze_torque * omega)) * dt
                return result(theta, {"final_angle_rad": theta, "final_angular_rate_rad_s": omega, "minimum_gap_m": min_gap, "squeeze_cutoff_m": cutoff, "dissipated_energy_j": dissipated, "edge_length_m": edge})
            """
        ),
        "05-y-shaped-pendulum": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                # Stage 1: reduced coupled-mode benchmark.
                mass = positive(data, "material_properties", "bob_mass_kg")
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                gravity = positive(data, "controls", "gravity_m_s2")
                kx = positive(data, "calibration_parameters", "stiffness_x_n_m")
                ky = positive(data, "calibration_parameters", "stiffness_y_n_m")
                kxy = value(data, "calibration_parameters", "cross_coupling_n_m")
                cx = max(0.0, value(data, "calibration_parameters", "damping_x_kg_s"))
                cy = max(0.0, value(data, "calibration_parameters", "damping_y_kg_s"))
                trace = (kx + ky) / mass
                split = math.sqrt(max(0.0, ((kx - ky) / mass) ** 2 + 4.0 * (kxy / mass) ** 2))
                omega_sq_1 = max(0.0, 0.5 * (trace - split))
                omega_sq_2 = max(0.0, 0.5 * (trace + split))
                omega_1 = math.sqrt(omega_sq_1)
                omega_2 = math.sqrt(omega_sq_2)
                closure_time = 2.0 * math.pi / max(abs(omega_2 - omega_1), 1.0e-12)
                q = [value(data, "initial_conditions", "bob_x0_m"), value(data, "initial_conditions", "bob_y0_m"), value(data, "initial_conditions", "bob_vx0_m_s"), value(data, "initial_conditions", "bob_vy0_m_s")]
                reduced_samples = []
                reduced_area = 0.0
                previous = q[:2]
                steps = max(1, int(duration / dt))
                sample_stride = max(1, steps // 24)
                def reduced_derivative(state: list[float]) -> list[float]:
                    x, y, vx, vy = state
                    ax = -(cx * vx + kx * x + kxy * y) / mass
                    ay = -(cy * vy + ky * y + kxy * x) / mass
                    return [vx, vy, ax, ay]
                for step in range(steps):
                    q = rk4(q, dt, reduced_derivative)
                    if step % sample_stride == 0:
                        reduced_samples.append({"x_m": q[0], "y_m": q[1], "time_s": (step + 1) * dt})
                        reduced_area += 0.5 * (previous[0] * q[1] - previous[1] * q[0])
                        previous = q[:2]

                # Stage 2: effective 2D projection of the constrained Y-string
                # network.  Tension-only penalty links make slack explicit while
                # keeping the fixture dependency-free and replaceable.
                half = positive(data, "geometry", "support_half_spacing_m")
                junction_z = value(data, "geometry", "junction_rest_z_m")
                bob_z = value(data, "geometry", "bob_rest_z_m")
                upper_left = positive(data, "geometry", "upper_left_length_m")
                upper_right = positive(data, "geometry", "upper_right_length_m")
                lower = positive(data, "geometry", "lower_length_m")
                junction_mass = positive(data, "material_properties", "junction_mass_kg")
                string_k = positive(data, "calibration_parameters", "constraint_stiffness_n_m")
                string_c = max(0.0, value(data, "calibration_parameters", "constraint_damping_kg_s"))
                planar_damping = 0.02 * (cx + cy)
                state = [value(data, "initial_conditions", "junction_x0_m"), value(data, "initial_conditions", "junction_y0_m"), value(data, "initial_conditions", "bob_x0_m"), value(data, "initial_conditions", "bob_y0_m"), value(data, "initial_conditions", "junction_vx0_m_s"), value(data, "initial_conditions", "junction_vy0_m_s"), value(data, "initial_conditions", "bob_vx0_m_s"), value(data, "initial_conditions", "bob_vy0_m_s")]
                max_tension = 0.0
                slack_events = 0
                last_slack = (False, False, False)
                constrained_samples = []
                def link_force(px: float, py: float, pz: float, vx: float, vy: float, ex: float, ey: float, ez: float, rest: float) -> tuple[float, float, float, bool]:
                    dx, dy, dz = ex - px, ey - py, ez - pz
                    length = max(math.sqrt(dx * dx + dy * dy + dz * dz), 1.0e-12)
                    rate = (dx * (-vx) + dy * (-vy)) / length
                    tension = string_k * max(0.0, length - rest) + string_c * max(0.0, rate)
                    return tension * dx / length, tension * dy / length, tension, tension <= 0.0
                def constrained_derivative(current: list[float]) -> list[float]:
                    jx, jy, bx, by, jvx, jvy, bvx, bvy = current
                    fl = link_force(jx, jy, junction_z, jvx, jvy, -half, 0.0, 0.0, upper_left)
                    fr = link_force(jx, jy, junction_z, jvx, jvy, half, 0.0, 0.0, upper_right)
                    fb = link_force(jx, jy, junction_z, jvx, jvy, bx, by, bob_z, lower)
                    jfx = fl[0] + fr[0] - fb[0] - planar_damping * jvx
                    jfy = fl[1] + fr[1] - fb[1] - planar_damping * jvy
                    bfx = fb[0] - planar_damping * bvx
                    bfy = fb[1] - planar_damping * bvy
                    return [jvx, jvy, bvx, bvy, jfx / junction_mass, jfy / junction_mass, bfx / mass, bfy / mass]
                for step in range(steps):
                    state = rk4(state, dt, constrained_derivative)
                    if not all(math.isfinite(item) for item in state):
                        raise ValueError("constrained Y-string state became non-finite")
                    jx, jy, bx, by, jvx, jvy, bvx, bvy = state
                    links = [link_force(jx, jy, junction_z, jvx, jvy, -half, 0.0, 0.0, upper_left), link_force(jx, jy, junction_z, jvx, jvy, half, 0.0, 0.0, upper_right), link_force(jx, jy, junction_z, jvx, jvy, bx, by, bob_z, lower)]
                    max_tension = max(max_tension, *(item[2] for item in links))
                    slack = tuple(item[3] for item in links)
                    slack_events += sum(current and not previous for current, previous in zip(slack, last_slack))
                    last_slack = slack
                    if step % sample_stride == 0:
                        constrained_samples.append({"time_s": (step + 1) * dt, "junction_x_m": jx, "junction_y_m": jy, "bob_x_m": bx, "bob_y_m": by})
                return result(closure_time, {"reduced_modal_frequencies_rad_s": [omega_1, omega_2], "frequency_ratio": omega_2 / max(omega_1, 1.0e-12), "closure_time_s": closure_time, "reduced_trajectory_samples": reduced_samples, "reduced_lissajous_area_m2": reduced_area, "constrained_final_bob_position_m": [state[2], state[3], bob_z], "constrained_max_tension_n": max_tension, "constrained_slack_events": slack_events, "constrained_trajectory_samples": constrained_samples, "gravity_m_s2": gravity, "closure_label": "provisional effective constrained network; replace penalty links with measured string constitutive closure"})
            """
        ),
        "07-sinking-funnel": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                gravity = positive(data, "controls", "gravity_m_s2")
                mass = positive(data, "material_properties", "funnel_mass_kg")
                rho = positive(data, "material_properties", "water_density_kg_m3")
                volume = positive(data, "geometry", "displaced_volume_m3")
                internal_area = positive(data, "geometry", "internal_area_m2")
                water_depth = positive(data, "geometry", "water_depth_m")
                added = max(0.0, value(data, "calibration_parameters", "added_mass_kg"))
                heave_damping = max(0.0, value(data, "calibration_parameters", "heave_damping_n_s_m"))
                heave_stiffness = max(0.0, value(data, "calibration_parameters", "heave_stiffness_n_m"))
                inertance = positive(data, "calibration_parameters", "hydraulic_inertance_pa_s2_m3")
                resistance = max(0.0, value(data, "calibration_parameters", "hydraulic_resistance_pa_s2_m6"))
                pitch_inertia = positive(data, "calibration_parameters", "pitch_inertia_kg_m2")
                pitch_damping = max(0.0, value(data, "calibration_parameters", "pitch_damping_n_m_s"))
                pitch_stiffness = max(0.0, value(data, "calibration_parameters", "pitch_stiffness_n_m"))
                flow_coupling = value(data, "calibration_parameters", "flow_coupling_n_s_m3")
                pitch_coupling = value(data, "calibration_parameters", "pitch_coupling_n_m_s")
                tip_limit = positive(data, "calibration_parameters", "tip_limit_rad")
                state = [value(data, "initial_conditions", "z0_m"), value(data, "initial_conditions", "dz0_m_s"), value(data, "initial_conditions", "eta0_m"), value(data, "initial_conditions", "flow0_m3_s"), value(data, "initial_conditions", "pitch0_rad"), value(data, "initial_conditions", "pitch_rate0_rad_s")]
                samples = []
                max_pitch = abs(state[4])
                max_immersion = abs(state[0])
                max_flow = abs(state[3])
                steps = max(1, int(duration / dt))
                sample_stride = max(1, steps // 32)
                def derivative(current: list[float]) -> list[float]:
                    z, dz, eta, flow, pitch, pitch_rate = current
                    buoyancy = rho * gravity * volume
                    heave_force = buoyancy - mass * gravity - heave_damping * dz - heave_stiffness * z - flow_coupling * flow
                    dz_dot = heave_force / max(mass + added, 1.0e-12)
                    pressure_drive = rho * gravity * (z - eta)
                    flow_dot = (pressure_drive - resistance * flow * abs(flow) - flow_coupling * dz) / inertance
                    eta_dot = (flow - internal_area * dz) / internal_area
                    pitch_accel = (-pitch_damping * pitch_rate - pitch_stiffness * pitch + pitch_coupling * flow) / pitch_inertia
                    return [dz, dz_dot, eta_dot, flow_dot, pitch_rate, pitch_accel]
                for step in range(steps):
                    state = rk4(state, dt, derivative)
                    state[0] = clamp(state[0], -water_depth, water_depth)
                    state[2] = clamp(state[2], -water_depth, water_depth)
                    state[3] = clamp(state[3], -0.05, 0.05)
                    state[4] = clamp(state[4], -2.0, 2.0)
                    max_pitch = max(max_pitch, abs(state[4]))
                    max_immersion = max(max_immersion, abs(state[0]))
                    max_flow = max(max_flow, abs(state[3]))
                    if step % sample_stride == 0:
                        samples.append({"time_s": (step + 1) * dt, "heave_z_m": state[0], "free_surface_eta_m": state[2], "flow_m3_s": state[3], "pitch_rad": state[4]})
                margin = tip_limit - max_pitch
                return result(margin, {"tipping_stability_margin_rad": margin, "max_abs_pitch_rad": max_pitch, "max_abs_heave_m": max_immersion, "max_abs_flow_m3_s": max_flow, "final_state": state, "trajectory_samples": samples, "topology": data.get("boundary_conditions", {}).get("topology", "open"), "closure_label": "provisional reduced heave/hydraulic/pitch model; native VOF case is exploratory and unexecuted"})
            """
        ),
        "11-sound-isolation": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                pressure = positive(data, "controls", "source_pressure_pa")
                frequency = positive(data, "controls", "frequency_hz")
                rho = positive(data, "material_properties", "air_density_kg_m3")
                sound_speed = positive(data, "material_properties", "sound_speed_m_s")
                viscosity = positive(data, "material_properties", "kinematic_viscosity_m2_s")
                diffusivity = positive(data, "material_properties", "thermal_diffusivity_m2_s")
                gamma = positive(data, "material_properties", "gamma")
                width = positive(data, "geometry", "slit_width_m")
                height = positive(data, "geometry", "slit_height_m")
                thickness = positive(data, "geometry", "slit_thickness_m")
                source_area = positive(data, "geometry", "source_area_m2")
                receiver_area = positive(data, "geometry", "receiver_area_m2")
                end_correction = positive(data, "calibration_parameters", "end_correction_factor")
                base_resistance = max(0.0, value(data, "calibration_parameters", "base_resistance_pa_s_m3"))
                thermo_factor = max(0.0, value(data, "calibration_parameters", "thermoviscous_factor"))
                flanking = clamp(value(data, "calibration_parameters", "flanking_power_fraction"), 0.0, 1.0)
                omega = 2.0 * math.pi * frequency
                area = width * height
                delta_v = math.sqrt(2.0 * viscosity / omega)
                delta_t = math.sqrt(2.0 * diffusivity / omega)
                boundary_ratio = (delta_v + (gamma - 1.0) * delta_t) / width
                resistance = base_resistance * (1.0 + thermo_factor * boundary_ratio)
                effective_length = thickness + end_correction * width
                acoustic_mass = rho * effective_length / area
                cavity_compliance = max(receiver_area * thickness / (rho * sound_speed * sound_speed), 1.0e-18)
                impedance = complex(resistance, omega * acoustic_mass - 1.0 / (omega * cavity_compliance))
                volume_flow = pressure * area / impedance
                incident_power = 0.5 * pressure * pressure * source_area / (rho * sound_speed)
                transmitted_power = 0.5 * resistance * abs(volume_flow) ** 2
                total_power = transmitted_power + flanking * incident_power
                lumped_tl = 10.0 * math.log10(max(incident_power / max(transmitted_power, 1.0e-18), 1.0e-18))
                thermoviscous_tl = 10.0 * math.log10(max(incident_power / max(total_power, 1.0e-18), 1.0e-18))
                return result(thermoviscous_tl, {"lumped_tl_db": lumped_tl, "thermoviscous_tl_db": thermoviscous_tl, "boundary_layer_ratio": boundary_ratio, "viscous_boundary_layer_m": delta_v, "thermal_boundary_layer_m": delta_t, "slit_area_m2": area, "effective_length_m": effective_length, "acoustic_impedance_pa_s_m3": [impedance.real, impedance.imag], "volume_flow_m3_s": [volume_flow.real, volume_flow.imag], "incident_power_w": incident_power, "transmitted_power_w": transmitted_power, "flanking_power_fraction": flanking, "closure_label": "reduced aperture/acoustic impedance with explicit thermoviscous correction; FEM and flanking paths remain unexecuted"})
            """
        ),
        "16-magnetic-carousel": textwrap.dedent(
            """
            def compute(data: dict[str, Any]) -> dict[str, Any]:
                drive = value(data, "controls", "drive_rate_rad_s")
                duration = positive(data, "controls", "duration_s")
                dt = positive(data, "controls", "time_step_s")
                count = integer(data, "controls", "array_count")
                mass = positive(data, "material_properties", "ball_mass_kg")
                inertia = positive(data, "material_properties", "ball_inertia_kg_m2")
                mu_static = max(0.0, value(data, "material_properties", "static_friction"))
                mu_kinetic = max(0.0, value(data, "material_properties", "kinetic_friction"))
                radius = positive(data, "geometry", "array_radius_m")
                ball_radius = positive(data, "geometry", "ball_radius_m")
                potential = positive(data, "calibration_parameters", "magnetic_potential_j")
                resisting = max(0.0, value(data, "calibration_parameters", "radial_resisting_torque_nm"))
                harmonic = value(data, "calibration_parameters", "magnetic_harmonic_fraction")
                gravity = 9.81
                state = [value(data, "initial_conditions", "carousel_angle_rad"), value(data, "initial_conditions", "ball_angle_rad"), value(data, "initial_conditions", "ball_rate_rad_s"), value(data, "initial_conditions", "ball_spin_rad_s")]
                steps = max(1, int(duration / dt))
                rate_sum = 0.0
                phase_sum = 0.0
                slip_steps = 0
                samples = []
                def force_map(phase: float) -> float:
                    # Staged harmonic map: replace with measured/FEM force-map
                    # interpolation without changing the contact workflow.
                    return (count * potential / radius) * (math.sin(count * phase) + 2.0 * harmonic * math.sin(2.0 * count * phase))
                def derivative(current: list[float]) -> list[float]:
                    carousel_angle, ball_angle, ball_rate, ball_spin = current
                    phase = ball_angle - carousel_angle
                    magnetic_torque = force_map(phase) * radius
                    slip_speed = radius * drive - ball_radius * ball_spin
                    slip_sign = 1.0 if slip_speed > 1.0e-10 else -1.0 if slip_speed < -1.0e-10 else 0.0
                    friction_force = (mu_kinetic if slip_sign else mu_static) * mass * gravity * slip_sign
                    orbit_friction_torque = friction_force * radius
                    spin_torque = friction_force * ball_radius
                    orbit_inertia = max(mass * radius * radius, 1.0e-12)
                    ball_accel = (magnetic_torque + orbit_friction_torque - resisting * math.tanh(ball_rate)) / orbit_inertia
                    spin_accel = spin_torque / inertia
                    return [drive, ball_rate, ball_accel, spin_accel]
                sample_stride = max(1, steps // 32)
                for step in range(steps):
                    state = rk4(state, dt, derivative)
                    state[2] = clamp(state[2], -50.0, 50.0)
                    state[3] = clamp(state[3], -500.0, 500.0)
                    phase = math.atan2(math.sin(state[1] - state[0]), math.cos(state[1] - state[0]))
                    rate_sum += state[2]
                    phase_sum += phase
                    slip_speed = radius * drive - ball_radius * state[3]
                    if abs(slip_speed) > 1.0e-10:
                        slip_steps += 1
                    if step % sample_stride == 0:
                        samples.append({"time_s": (step + 1) * dt, "carousel_angle_rad": state[0], "ball_angle_rad": state[1], "ball_rate_rad_s": state[2], "ball_spin_rad_s": state[3], "phase_rad": phase})
                mean_rate = rate_sum / steps
                mean_phase = phase_sum / steps
                direction = "locked" if abs(mean_rate - drive) < 0.05 * max(abs(drive), 1.0) else "same" if mean_rate * drive >= 0.0 else "opposite"
                return result(mean_rate, {"mean_ball_rate_rad_s": mean_rate, "mean_phase_lag_rad": mean_phase, "slip_fraction": slip_steps / steps, "direction": direction, "force_map_samples_nm": [force_map(2.0 * math.pi * index / (count * 16.0)) * radius for index in range(count * 16)], "final_state": state, "trajectory_samples": samples, "contact_workflow": "force-map stage -> rolling/sliding contact dynamics -> drift-direction diagnostic", "closure_label": "provisional harmonic force map; replace with measured lookup map and escalate only if its falsifier fails"})
            """
        ),
    }
    footer = "\n\nif __name__ == \"__main__\":\n    raise SystemExit(\"import compute(data) from this module\")\n"
    return header + bodies[case_id] + footer


def _extractor_source() -> str:
    return """#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def extract_results(raw_path: Path, output_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    value = raw.get("value")
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("raw output lacks a finite primary observable")
    outputs = raw.get("outputs", {})
    if not isinstance(outputs, dict):
        raise ValueError("raw output outputs must be an object")
    result = {
        "case_id": raw.get("case_id"),
        "observable": raw.get("observable"),
        "value": float(value),
        "unit": raw.get("unit", "SI"),
        "equation_id": raw.get("equation_id"),
        "equation_ids": raw.get("equation_ids", []),
        "synthetic": bool(raw.get("synthetic")),
        "outputs": outputs,
        "validation_state": "runnable_synthetic",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2) + "\\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, default=Path("outputs/raw.json"))
    parser.add_argument("--output", type=Path, default=Path("outputs/results.json"))
    args = parser.parse_args()
    print(json.dumps(extract_results(args.raw, args.output), indent=2))
"""


def _route_test_source(case_id: str) -> str:
    checks = {
        "01-pinhole-sunglasses": "limit = json.loads(json.dumps(data)); limit[\"controls\"][\"delta_p_m_inv\"] = 0.0; assert limit[\"controls\"][\"pinhole_diameter_m\"] > 0.0; assert compute(limit)[\"outputs\"][\"optimal_pinhole_diameter_m\"] == 0.0",
        "02-disc-spectrometer": "assert abs(sum(result[\"outputs\"][\"line_profile\"]) - 1.0) < 1e-12",
        "04-singing-capacitor": "limit = json.loads(json.dumps(data)); limit[\"controls\"][\"drive_voltage_v\"] = 0.0; assert abs(compute(limit)[\"value\"]) < 1e-18",
        "06-seeing-sound": "limit = json.loads(json.dumps(data)); limit[\"controls\"][\"drive_pressure_pa\"] = 0.0; assert abs(compute(limit)[\"value\"]) < 1e-18",
        "08-upward-driven-disc": "limit = json.loads(json.dumps(data)); limit[\"controls\"][\"forcing_amplitude\"] = 0.0; limit[\"initial_conditions\"].update({\"y0\": 0.0, \"z0\": 0.0, \"omega0\": 0.0}); zero = compute(limit); assert abs(zero[\"value\"]) < 1e-12 and abs(zero[\"outputs\"][\"final_z\"]) < 1e-12",
        "09-photographic-bokeh": "limit = json.loads(json.dumps(data)); limit[\"initial_conditions\"][\"defocus_m\"] = 0.0; assert compute(limit)[\"outputs\"][\"bokeh_radius_m\"] == 0.0",
        "10-air-vortex": "limit = json.loads(json.dumps(data)); limit[\"controls\"][\"slip_factor\"] = 0.0; assert compute(limit)[\"outputs\"][\"vortex_depth_m\"] == 0.0",
        "12-dotted-line-trick": "assert result[\"outputs\"][\"stored_spring_energy_j\"] >= 0.0 and result[\"outputs\"][\"stick_slip_period_s\"] > 0.0",
        "15-cold-drink": "assert result[\"outputs\"][\"lowest_drink_temperature_k\"] <= data[\"initial_conditions\"][\"drink_temperature_k\"]",
        "17-falling-book-cover": "limit = json.loads(json.dumps(data)); limit[\"controls\"][\"motor_torque_nm\"] = 0.0; limit[\"initial_conditions\"].update({\"theta0_rad\": 0.0, \"omega0_rad_s\": 0.0}); assert abs(compute(limit)[\"value\"]) < 1e-12",
        "05-y-shaped-pendulum": "assert result[\"outputs\"][\"closure_time_s\"] > 0.0 and result[\"outputs\"][\"constrained_slack_events\"] >= 0 and all(math.isfinite(item) for item in result[\"outputs\"][\"constrained_final_bob_position_m\"])",
        "07-sinking-funnel": "assert math.isfinite(result[\"outputs\"][\"tipping_stability_margin_rad\"]) and result[\"outputs\"][\"trajectory_samples\"]",
        "11-sound-isolation": "assert result[\"outputs\"][\"boundary_layer_ratio\"] > 0.0 and math.isfinite(result[\"outputs\"][\"thermoviscous_tl_db\"])",
        "16-magnetic-carousel": "assert math.isfinite(result[\"outputs\"][\"mean_ball_rate_rad_s\"]) and 0.0 <= result[\"outputs\"][\"slip_fraction\"] <= 1.0 and len(result[\"outputs\"][\"force_map_samples_nm\"]) >= 16",
    }[case_id]
    return textwrap.dedent(
        f"""
        import json
        import math
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.model import compute

        data = json.loads((Path(__file__).resolve().parents[1] / "examples" / "synthetic.json").read_text(encoding="utf-8"))
        result = compute(data)
        assert result["synthetic"] is True
        assert math.isfinite(result["value"])
        assert result["outputs"]
        {checks}
        """
    ).lstrip()


def _parameter_specs(case_id: str, inputs: dict[str, Any]) -> list[dict[str, str]]:
    units = UNIT_MAP[case_id]
    rows: list[dict[str, str]] = []
    for category, values in inputs.items():
        for name in values:
            rows.append({"parameter": name, "category": category, "unit": units.get(name, "1"), "provenance": "synthetic fixture; replace with measured value and source", "role": "measured control or geometry input"})
    return rows


def _example(case_id: str, measured: bool = False) -> dict[str, Any]:
    inputs = json.loads(json.dumps(_case_inputs()[case_id]))
    inputs.update({"derived_quantities": {}, "state_variables": {}, "observables": {}, "uncertainties": {}})
    for row in _parameter_specs(case_id, _case_inputs()[case_id]):
        inputs["uncertainties"][row["parameter"]] = {"unit": row["unit"], "standard_uncertainty": 0.01, "source": "synthetic fixture placeholder"}
    inputs["metadata"] = {"case_id": case_id, "route": CASE_META[case_id]["route"], "synthetic": not measured, "measured": measured, "provenance": "" if not measured else "user-supplied measurement log and calibration record"}
    return inputs


def _parameter_template(case_id: str, primary_solver: str, route: str) -> dict[str, Any]:
    inputs = _case_inputs()[case_id]
    output: dict[str, Any] = {"case_id": case_id, "primary_solver": primary_solver, "route": route, "input_contract_version": 1, "required_input_categories": ["measured_controls", "geometry", "material_properties", "initial_conditions", "boundary_conditions", "fitted_calibration_values", "uncertainties"]}
    for source, target in (("controls", "measured_controls"), ("calibration_parameters", "fitted_calibration_values")):
        output[target] = {name: {"value": None, "unit": UNIT_MAP[case_id].get(name, "1"), "provenance": "replace with measured/calibrated value", "uncertainty_required": True} for name in inputs[source]}
    for category in ("geometry", "material_properties", "initial_conditions", "boundary_conditions"):
        output[category] = {name: {"value": None, "unit": UNIT_MAP[case_id].get(name, "1"), "provenance": "replace with apparatus record", "uncertainty_required": True} for name in inputs[category]}
    output["uncertainties"] = {name: {"unit": UNIT_MAP[case_id].get(name, "1"), "standard_uncertainty": None, "source": "required measurement/calibration record"} for row in _parameter_specs(case_id, inputs) for name in [row["parameter"]]}
    output["derived_quantities"] = {}
    output["state_variables"] = {}
    output["observables"] = {}
    output["notes"] = ["Derived quantities, solver states and observables are outputs, not required inputs.", "Imported measured fields require a nonempty provenance record and uncertainty."]
    return output


def _mapping_rows(case_id: str, meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _parameter_specs(case_id, _case_inputs()[case_id]):
        rows.append({"parameter": row["parameter"], "destination_kind": f"{meta['solver']} input category", "destination": f"src/model.py:compute -> {row['category']}.{row['parameter']}", "equation_id": meta["equations"][0], "implemented_file": "src/model.py", "implemented_symbol": "compute", "units": row["unit"], "notation_conversion": f"{row['parameter']} is read from the separated {row['category']} category without treating outputs as inputs", "discretization_or_approximation": "dependency-free deterministic synthetic benchmark; external route uses the native adapter and is not executed here", "implementation_assumptions": ["finite SI-valued input", "synthetic fixture is not apparatus evidence"]})
    return rows


def _equation_lineage(case_id: str, meta: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for equation_id in meta["equations"]:
        rows.append({"equation_id": equation_id, "source_locator": f"../theory/equations.yaml#{equation_id}", "original_equation": f"registered IYPT 2027 equation id: {equation_id}", "implemented_file": "src/model.py", "implemented_symbol": "compute", "notation_conversion": "registered symbols are mapped to explicit separated-input names", "units": "SI units declared in parameter-template.json and parameter-map.json", "discretization_or_approximation": "deterministic synthetic reduction; native solver discretization remains a separate production step", "implementation_assumptions": ["selected model assumptions are unchanged", "synthetic values are used only for software smoke testing"]})
    return {"case_id": case_id, "equations": rows}


def _native_overrides(package: Path, case_id: str, meta: dict[str, Any]) -> None:
    route = meta["route"]
    if case_id == "05-y-shaped-pendulum":
        _write(package / "native" / "chrono_case.py", textwrap.dedent('''
            """Native Project Chrono adapter for the provisional Y-string workflow.

            The force law is intentionally replaceable: the synthetic package
            uses the same topology with a dependency-free penalty link, while
            this adapter is the external Chrono entry point for measured
            geometry, unilateral strings and contact/tension diagnostics.
            """
            import pychrono as chrono

            def build_system():
                system = chrono.ChSystemNSC()
                system.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -9.81))
                # Replace fixture dimensions from examples/apparatus-template.json.
                return system

            def run_dynamics():
                system = build_system()
                # Populate measured bodies and unilateral links before using
                # this deterministic integrator/output loop.
                for _ in range(100):
                    system.DoStepDynamics(0.001)
                raise RuntimeError("populate measured Y-string geometry before native execution")
        ''').lstrip(), True)
        _write(package / "native" / "closure-notes.md", "# Y-string native closure\n\nThe reduced modal benchmark and penalty-link synthetic path are exploratory. Replace effective stiffness, rest lengths, tension law and slack transition with measured or derived closure before Chrono execution.\n")
        return
    if case_id == "07-sinking-funnel":
        _write(package / "native" / "system" / "controlDict", textwrap.dedent("""
            application     interFoam;
            startFrom       startTime;
            startTime       0;
            endAt           endTime;
            endTime         2;
            deltaT          0.002;
            writeControl    timeStep;
            writeInterval   100;
            // Provisional open-funnel free-surface route. Map measured geometry,
            // inlet/outlet topology, wetting and closure coefficients before run.
        """).lstrip())
        _write(package / "native" / "Allrun", "#!/usr/bin/env bash\nset -euo pipefail\ncase_dir=\"$(cd \"$(dirname \"$0\")\" && pwd)/..\"\ncommand -v blockMesh\ncommand -v checkMesh\ncommand -v interFoam\nblockMesh -case \"$case_dir\"\ncheckMesh -case \"$case_dir\"\ninterFoam -case \"$case_dir\"\n", True)
        _write(package / "native" / "free-surface-closures.md", "# Sinking-funnel CFD closures\n\nThe target is an exploratory `interFoam` free-surface case. Synthetic smoke testing does not solve VOF. Before native execution, document funnel topology, entrained-air state, wetting/contact angle, inlet/outlet pressure, turbulence treatment, and measured inertance/resistance closure.\n")
        return
    if case_id == "11-sound-isolation":
        _write(package / "native" / "case.sif", textwrap.dedent("""
            Header
              CHECK KEYWORDS Warn
            End

            Simulation
              Max Output Level = 3
              Simulation Type = Harmonic
              Coordinate System = Cartesian 2D
              Mesh DB = "mesh" "iypt2027_sound_slit"
            End

            Constants
              Density Of Air = 1.2
              Sound Speed = 343
            End

            Body 1
              Name = "provisional slit partition"
              Equation = 1
            End

            Equation 1
              Name = "harmonic acoustic slit route"
              Active Solvers(1) = 1
            End

            Solver 1
              Equation = Wave Equation
              Procedure = "AcousticSolve" "AcousticSolver"
              Variable = Pressure
              Angular Frequency = 5026.548
            End

            ! Thermoviscous correction and flanking boundary choices are recorded
            ! in parameter-map.json and native/thermoviscous-sl it.geo.
        """).replace("thermoviscous-sl it", "thermoviscous-slit").lstrip())
        _write(package / "native" / "thermoviscous-slit.geo", "Point(1) = {0, 0, 0, 0.0005};\nPoint(2) = {0.04, 0, 0, 0.0005};\nPoint(3) = {0.04, 0.05, 0, 0.0005};\nPoint(4) = {0, 0.05, 0, 0.0005};\nLine(1) = {1, 2};\nLine(2) = {2, 3};\nLine(3) = {3, 4};\nLine(4) = {4, 1};\nLine Loop(1) = {1, 2, 3, 4};\nPlane Surface(1) = {1};\n")
        _write(package / "native" / "closure-notes.md", "# Sound-isolation FEM closures\n\nThe reduced impedance model is the executable baseline. The Elmer route is a higher-fidelity harmonic adapter; thermoviscous wall losses, end correction, cavity compliance and flanking paths require measured/derived closure before execution.\n")
        return
    if case_id == "16-magnetic-carousel":
        _write(package / "native" / "chrono_case.py", textwrap.dedent('''
            """Native Project Chrono adapter for staged magnetic-map/contact dynamics."""
            import pychrono as chrono

            def build_system(force_map_csv="force-map.csv"):
                system = chrono.ChSystemNSC()
                system.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -9.81))
                # Load a measured or FEM force map, then apply interpolation
                # forces and rolling/sliding contact to the ball body.
                return system

            def run_dynamics():
                system = build_system()
                # Populate the force-map callback and contact bodies before
                # using this deterministic integrator/output loop.
                for _ in range(100):
                    system.DoStepDynamics(0.001)
                raise RuntimeError("provide a measured/FEM force map before native execution")
        ''').lstrip(), True)
        _write(package / "native" / "force-map-workflow.md", "# Magnetic carousel force-map workflow\n\nStage 1: measure or compute force versus relative phase and gap. Stage 2: interpolate the map in the Chrono force callback. Stage 3: resolve rolling/sliding contact and compare mean rate, phase lag, slip fraction and direction. Escalate to coupled magnetodynamics only if the quasi-static map falsifier fails.\n")
        return
    if route == "fourier_optics":
        _write(package / "native" / "hcipy_config.py", textwrap.dedent(f"""
            \"\"\"Native HCIPy array path for {case_id}; not executed in this archive.\"\"\"
            from hcipy import FraunhoferPropagator, Wavefront, make_circular_aperture, make_pupil_grid

            wavelength_m = 5.5e-7
            grid_points = 128
            aperture_diameter_m = 0.01
            grid = make_pupil_grid(grid_points, aperture_diameter_m)
            aperture = make_circular_aperture(aperture_diameter_m)(grid)
            propagator = FraunhoferPropagator(grid, focal_length=0.1)
            wavefront = Wavefront(aperture, wavelength=wavelength_m)
            # Production runs must replace these fixture values from the separated input file.
        """).lstrip())
    elif route == "elmer_fem":
        _write(package / "native" / "case.sif", textwrap.dedent(f"""
            Header
              CHECK KEYWORDS Warn
            End

            Simulation
              Max Output Level = 3
              Simulation Type = Harmonic
              Coordinate System = Cartesian 3D
              Mesh DB = "mesh" "iypt2027"
            End

            Constants
              Gravity(4) = 0 0 -9.81 0
            End

            Body 1
              Name = "finite apparatus"
              Equation = 1
              Material = 1
            End

            Material 1
              Name = "measured material placeholder"
              Youngs Modulus = 2.0e9
              Density = 1200
              Poisson Ratio = 0.3
            End

            Equation 1
              Name = "route-specific coupled equation"
              Active Solvers(1) = 1
            End

            Solver 1
              Procedure = "StressSolve" "StressSolver"
              Variable = Displacement
              Calculate Stresses = True
              Steady State Convergence Tolerance = 1.0e-8
            End

            Boundary Condition 1
              Name = "measured drive and apparatus boundary"
              Target Boundaries(1) = 1
              Displacement 1 = 0
              Displacement 2 = 0
              Displacement 3 = 0
            End

            ! Parameter mapping and forcing conventions are in parameter-map.json.
        """).lstrip())
        _write(package / "native" / "mesh_generator.py", textwrap.dedent(f"""
            from pathlib import Path

            CASE_ID = {case_id!r}

            def write_mesh_instructions(output: Path = Path("mesh")) -> None:
                output.mkdir(parents=True, exist_ok=True)
                (output / "README.txt").write_text(
                    "Generate the finite apparatus mesh from native/beam.geo, then run ElmerGrid and ElmerSolver.\\n",
                    encoding="utf-8",
                )

            if __name__ == "__main__":
                write_mesh_instructions()
        """).lstrip(), True)
        _write(package / "native" / "beam.geo", "Point(1) = {0, 0, 0, 0.005};\nPoint(2) = {0.01, 0, 0, 0.005};\nPoint(3) = {0.01, 0.004, 0, 0.005};\nPoint(4) = {0, 0.004, 0, 0.005};\nLine(1) = {1, 2};\nLine(2) = {2, 3};\nLine(3) = {3, 4};\nLine(4) = {4, 1};\nLine Loop(1) = {1, 2, 3, 4};\nPlane Surface(1) = {1};\n")
    elif route == "project_chrono":
        _write(package / "native" / "chrono_case.py", textwrap.dedent(f"""
            \"\"\"Native Project Chrono adapter for {case_id}; external execution is unverified.\"\"\"
            import pychrono as chrono

            def build_system():
                system = chrono.ChSystemNSC()
                system.SetGravitationalAcceleration(chrono.ChVector3d(0, -9.81, 0))
                body = chrono.ChBodyEasyBox(0.3, 0.01, 0.12, 500)
                body.SetBodyFixed(False)
                body.SetPos(chrono.ChVector3d(0, 0, 0))
                system.AddBody(body)
                # Bodies, constraints, forces, contact and output channels must be
                # replaced from the measured input template before production use.
                return system, body

            def run_dynamics(output_path="chrono-output.csv"):
                system, body = build_system()
                with open(output_path, "w", encoding="utf-8") as stream:
                    stream.write("time_s,position_y_m,velocity_y_m_s\\n")
                    for index in range(101):
                        time_s = index * 0.001
                        stream.write(f"{{time_s}},{{body.GetPos().y}},0\\n")
                        system.DoStepDynamics(0.001)

            if __name__ == "__main__":
                run_dynamics()
        """).lstrip(), True)
    elif route == "openfoam_continuum":
        _write(package / "native" / "system" / "controlDict", textwrap.dedent(f"""
            application     interFoam;
            startFrom       startTime;
            startTime       0;
            endAt           endTime;
            endTime         0.2;
            deltaT          0.001;
            writeControl    timeStep;
            writeInterval   100;
            // {case_id}: map stirrer_angular_rate_rad_s and slip_factor to the fluid motion.
            // The onset observable is extracted from the free-surface field, not supplied as an input.
        """).lstrip())
        _write(package / "native" / "Allrun", "#!/usr/bin/env bash\nset -euo pipefail\ncase_dir=\"$(cd \"$(dirname \"$0\")\" && pwd)/..\"\ncommand -v blockMesh\ncommand -v checkMesh\ncommand -v interFoam\nblockMesh -case \"$case_dir\"\ncheckMesh -case \"$case_dir\"\ninterFoam -case \"$case_dir\"\n", True)


def _package_readme(case_id: str, meta: dict[str, Any]) -> str:
    provisional_note = ""
    if meta.get("provisional_model"):
        provisional_note = textwrap.dedent(f"""

        ## Amendment 05 provisional boundary

        This package is `runnable_provisional`: it executes a reduced and/or
        replaceable-closure model with synthetic parameters so the code path,
        numerical pipeline and output contract can be smoke-tested. The
        scientific readiness remains `model_selected_not_closed`. The explicit
        missing closures are: {"; ".join(meta.get("known_missing_physics", []))}.
        No apparatus-level fidelity, predictive accuracy, external-solver
        execution, numerical verification or experimental validation is claimed.
        """)
    return textwrap.dedent(f"""
        # IYPT 2027 `{case_id}` Linux simulation package

        Wave: **{meta['wave']}**. Route: **{meta['route']}**. Primary solver: **{meta['solver']}**.

        This package contains a case-specific implementation, separated
        inputs, a synthetic fixture, a case generator, an extractor, tests, and
        a native adapter for the selected external route. The synthetic path is
        dependency-free Python and is only software evidence. The external
        solver has not been installed or executed in this archive, and no
        numerical convergence or experimental validity is claimed.

        ## Beginner Ubuntu path

        ```bash
        cd linux-simulation
        bash check_system.sh --mode synthetic
        bash run_gate.sh
        bash run.sh
        cat outputs/results.json
        cat receipts/synthetic-smoke.json
        ```

        `bash run.sh --apparatus examples/apparatus-template.json` is blocked
        until the template is filled with measured values, provenance and
        uncertainty records. Production mode additionally requires the named
        external solver and a generated native case.

        Optional dependencies and version targets are recorded in
        `requirements.txt`, `environment.yml` and `dependency_report.yaml` at
        the case root. Do not treat a successful synthetic run as evidence that
        `{meta['solver']}` is installed or that the apparatus model is validated.

        ## Input/output boundary

        Required inputs are separated into measured controls, geometry, material
        properties, initial conditions, boundary conditions, fitted calibration
        values and uncertainties. Derived quantities, solver state variables and
        observables are outputs. The registered observable is:

        `{meta['observable']}`

        Equation IDs used by the implementation are: `{', '.join(meta['equations'])}`.
        Concrete mappings and source-to-code lineage are in `parameter-map.json`
        and `equation-lineage.json`.

        ## Verification boundary

        `numerical-verification.json` defines three route-specific refinement
        levels, an observable, metric, tolerance and limiting behavior. It is
        intentionally **unexecuted**. The receipt in `receipts/` proves only
        that the synthetic implementation, generator and extractor ran in this
        environment.
        {provisional_note}
    """).lstrip()


def _dependency_report(meta: dict[str, Any]) -> dict[str, Any]:
    limitations = ["Synthetic smoke receipt is software evidence only.", f"{meta['solver']} native execution, numerical verification and experimental comparison remain unexecuted."]
    if meta.get("provisional_model"):
        limitations.extend(meta.get("closure_blockers", []))
    return {"mode": "reduced_capability", "dependencies": [{"name": meta["solver"], "available": False, "detail": "external solver not installed or executed in this archive"}, {"name": "Python standard library synthetic runtime", "available": True, "detail": "used by the dependency-free synthetic smoke path"}], "limitations": limitations}


def _handoff(case_id: str, meta: dict[str, Any], mappings: list[dict[str, Any]]) -> dict[str, Any]:
    scientific = meta.get("scientific_readiness", "model_closed")
    implementation_status = meta.get("implementation_status", "runnable_synthetic")
    provisional = bool(meta.get("provisional_model", False))
    meaning = "provisional synthetic implementation and extractor completed; external solver, apparatus fidelity and predictive claims remain gated" if provisional else "synthetic implementation and extractor completed; no external solver claim"
    return {"simulation_contract_version": 1, "primary_solver": meta["solver"], "version_policy": f"Target {meta['solver']} route version is recorded in the package manifest; external solver version is not executed in this archive.", "solver_distribution": "external_reference", "highest_state": "runnable_synthetic", "scientific_readiness": scientific, "software_readiness": "runnable_synthetic", "implementation_status": implementation_status, "provisional_model": provisional, "claim_ceiling": meta["claim"], "state_evidence": [{"state": "runnable_synthetic", "receipt": "linux-simulation/receipts/synthetic-smoke.json", "verified_at": "generated by the package command", "meaning": meaning}], "official_installation_source": meta["url"], "documentation_locator": f"Official {meta['solver']} documentation; see linux-simulation/README.md for the route boundary.", "parameter_mapping": mappings, "boundary_and_initial_conditions": ["Use measured apparatus geometry and controls only after the apparatus template is completed.", "Synthetic fixture uses finite values solely to exercise the implementation path."], "discretization_plan": "Run the three registered levels in numerical-verification.json after installing the external route; report mesh, sampling or time-step error separately from model-form error.", "controls": "Record exact input hash, package revision, external solver version, mesh/grid/time-step, tolerances, random seeds and output hashes.", "output_extraction": meta["observable"], "verification_plan": ["Run the registered zero/limit and dimensional checks.", "Perform three-level refinement on the registered observable before numerical claims.", "Compare held-out apparatus measurements with uncertainty-weighted residuals only after external execution."], "validation_plan": ["Trace each measured control through the package input, solver quantity and extracted observable.", "Keep measurement, numerical and model-form uncertainty separate; do not infer physical validity from synthetic output."], "validation_chain": [{"experiment_measurement": meta["observable"], "simulation_input": "measured controls, geometry, initial state, calibrated coefficients and uncertainties", "solver_quantity": meta["observable"], "output_metric": "absolute observable plus registered trend/falsifier metrics", "comparison_method": "uncertainty-weighted residuals on held-out parameter ranges", "uncertainty_treatment": "propagate measurement, calibration, discretization and model-form uncertainty separately", "acceptance_criterion": "registered limits pass and held-out residuals are compatible with the declared uncertainty model"}], "beginner_readme": "linux-simulation/README.md"}


def _project_state(case_id: str, exact_prompt: str, scientific: str, software: str, claim: str, stage: str, evidence: list[str]) -> dict[str, Any]:
    implementation_status = "runnable_provisional" if scientific == "model_selected_not_closed" and software == "runnable_synthetic" else None
    state = {"contract_version": 3, "simulation_contract_version": 1, "case_id": case_id, "exact_prompt": exact_prompt, "stage": stage, "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), "scientific_readiness": scientific, "software_readiness": software, "claim_ceiling": claim, "claims": [{"stage": stage, "status": "completed" if evidence else "blocked", "evidence_ids": evidence}]}
    if implementation_status:
        state["implementation_status"] = implementation_status
        state["provisional_model"] = True
    return state


def _update_implemented_case(case_id: str, generic: Any) -> None:
    case_dir = ARCHIVE / case_id
    meta = CASE_META[case_id]
    inputs = _case_inputs()[case_id]
    exact_prompt = _load_json(case_dir / "problem_contract.yaml")["exact_prompt"]
    mappings = _mapping_rows(case_id, meta)
    temp_root = Path(tempfile.mkdtemp(prefix=f"iypt2027-{case_id}-"))
    try:
        temp_package = temp_root / "linux-simulation"
        generic.generate_package(meta["route"], temp_package, model_id=meta["model_id"])
        target = case_dir / "linux-simulation"
        shutil.copytree(temp_package, target, dirs_exist_ok=True)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    package = case_dir / "linux-simulation"
    _write(package / "src" / "model.py", _model_source(case_id, meta["observable"], meta["equations"]))
    _write(package / "extract_results.py", _extractor_source(), True)
    _write(package / "tests" / "test_route_contract.py", _route_test_source(case_id))
    _write_json(package / "examples" / "synthetic.json", _example(case_id))
    _write_json(package / "examples" / "apparatus-template.json", _example(case_id, measured=False) | {"metadata": {"case_id": case_id, "route": meta["route"], "synthetic": False, "measured": False, "provenance": "", "instructions": "replace all fixture values, add field-level provenance and uncertainty before apparatus mode"}})
    _write_json(package / "parameter-map.json", {"case_id": case_id, "mappings": mappings})
    _write_json(package / "equation-lineage.json", _equation_lineage(case_id, meta))
    _write_json(package / "numerical-verification.json", {"case_id": case_id, "refinement_variable": {"fourier_optics": "array sampling and field-of-view", "elmer_fem": "mesh size and harmonic tolerance", "project_chrono": "time step and contact/integrator tolerance", "openfoam_continuum": "mesh size and time step", "python_ode": "time step and ODE tolerance"}.get(meta["route"], "route-specific numerical resolution"), "levels": [1.0, 0.5, 0.25], "observable": meta["observable"], "metric": "relative L2 or absolute error of the registered observable against the route limit/finest level", "tolerance": 1.0e-3, "expected_limiting_behavior": f"the {meta['equations'][-1]} observable is stable under the three declared refinement levels", "failure_interpretation": "implementation, units, native case generation or numerical resolution are not yet trustworthy; do not call this a physical-model failure", "executed": False, "status": "unexecuted", "receipt": None})
    _write(package / "numerical-verification.md", f"# Numerical verification: {case_id}\n\nThree levels are `1.0`, `0.5` and `0.25` of the declared route resolution. The observable is `{meta['observable']}` and the metric/tolerance are recorded in `numerical-verification.json`. This plan is unexecuted; the synthetic receipt is not numerical verification.\n")
    _write(package / "README.md", _package_readme(case_id, meta))
    _native_overrides(package, case_id, meta)
    scientific = meta.get("scientific_readiness", "model_closed")
    implementation_status = meta.get("implementation_status", "runnable_synthetic")
    provisional_model = bool(meta.get("provisional_model", False))
    _write_json(package / "simulation_package_manifest.json", {"package_version": 1, "simulation_contract_version": 1, "route": meta["route"], "model_id": meta["model_id"], "primary_solver": meta["solver"], "solver_version": {"HCIPy": "0.7.0 (external target; not executed)", "Elmer FEM": "9.0 (external target; not executed)", "Project Chrono": "10.0.0 (external target; not executed)", "OpenFOAM": "14 (external target; not executed)", "Python/SciPy": "NumPy 1.26.4 / SciPy 1.13.1 (external target; not executed)"}[meta["solver"]], "package_revision": PACKAGE_REVISION, "scientific_readiness": scientific, "software_readiness": "implementation_ready", "implementation_status": implementation_status, "provisional_model": provisional_model, "implementation": {"source_files": ["src/model.py"], "solver_native_files": sorted(path.relative_to(package).as_posix() for path in (package / "native").rglob("*") if path.is_file()) if (package / "native").is_dir() else [], "case_generator": "generate_case.py", "result_extractor": "extract_results.py"}, "entrypoints": {"check_system": "check_system.sh", "run_gate": "run_gate.sh", "generate_case": "generate_case.py", "run": "run.sh", "extract_results": "extract_results.py"}, "input_schema": "parameters.schema.json", "synthetic_example": "examples/synthetic.json", "numerical_verification": "numerical-verification.json", "parameter_mapping": mappings, "claim_ceiling": "implementation_ready only; synthetic smoke receipt not yet generated", "runnable_claim": False, "receipts": "receipts/"})
    _write_json(case_dir / "linux-simulation" / "parameter-template.json", _parameter_template(case_id, meta["solver"], meta["route"]))
    _write_json(case_dir / "dependency_report.yaml", _dependency_report(meta))

    # Route and handoff are kept synchronized with the implementation package.
    route = _load_json(case_dir / "simulation_route.yaml")
    route["selected_model_id"] = meta["model_id"]
    route["selected_route"] = meta["route"]
    route["primary_solver"] = meta["solver"]
    route["single_solver_baseline"] = f"{meta['solver']} implementation for the registered model; native execution remains evidence-gated."
    route["evidence_label"] = "exploratory"
    route["rationale"] = f"The selected {meta['solver']} route is implemented as a {'provisional exploratory package' if provisional_model else 'closed-model package'}, with a dependency-free synthetic benchmark and a separate native adapter."
    for stale_key in ("conditional_route", "conditional_solver", "closure_gate"):
        route.pop(stale_key, None)
    if meta.get("known_missing_physics"):
        route["known_missing_physics"] = list(meta["known_missing_physics"])
    if meta.get("closure_blockers"):
        route["provisional_closure_blockers"] = list(meta["closure_blockers"])
    route["implementation_status"] = implementation_status
    route["provisional_model"] = provisional_model
    if isinstance(route.get("selection_chain"), dict):
        route["selection_chain"]["solver"] = meta["solver"]
        route["selection_chain"]["numerical_requirements"] = list(route["selection_chain"].get("numerical_requirements", [])) + ["export the registered observable from an executable package", "keep provisional closure assumptions replaceable and evidence-labelled"]
    _write_json(case_dir / "simulation_route.yaml", route)
    spec = _load_json(case_dir / "simulation_spec.yaml")
    spec["selected_model_id"] = meta["model_id"]
    spec["route"] = meta["route"]
    for stale_key in ("conditional_route", "conditional_solver", "closure_gate"):
        spec.pop(stale_key, None)
    spec["execution_boundary"] = "synthetic package smoke-tested; external solver, apparatus fidelity, predictive accuracy and physical validation unexecuted"
    spec["implementation_status"] = implementation_status
    spec["provisional_model"] = provisional_model
    _write_json(case_dir / "simulation_spec.yaml", spec)
    registry = _load_json(case_dir / "model_registry.yaml")
    registry["selected_candidate_ids"] = [meta["model_id"]]
    registry["selection_outcome"] = "selected_working_baseline"
    registry["selection_rationale"] = f"Amendment 05 permits a {meta['route']} exploratory implementation for the plausible baseline; unresolved closures remain explicit and block apparatus/predictive claims."
    for candidate in registry.get("candidates", []):
        if isinstance(candidate, dict):
            candidate["status"] = "selected_working_baseline" if candidate.get("id") == meta["model_id"] else "retained_competitor"
            if candidate.get("id") == meta["model_id"]:
                candidate["implementation_status"] = implementation_status
                candidate["provisional_assumptions"] = list(meta.get("known_missing_physics", []))
    _write_json(case_dir / "model_registry.yaml", registry)
    requirements = _load_json(case_dir / "solver_requirements.yaml")
    requirements["model_closure_status"] = requirements.get("model_closure_status", "unresolved")
    requirements["provisional_implementation_allowed"] = provisional_model
    requirements["provisional_implementation_status"] = implementation_status
    requirements["closure_blockers"] = list(meta.get("closure_blockers", requirements.get("closure_blockers", [])))
    requirements["claim_boundary"] = "Synthetic code and native case generation may proceed for exploratory testing; apparatus fidelity, predictive accuracy, numerical verification and experimental validation remain blocked until closure evidence is added."
    _write_json(case_dir / "solver_requirements.yaml", requirements)
    equations = _load_json(case_dir / "theory" / "equations.yaml")
    equations["implementation_update"] = {"amendment": "05_IYPT_2027_SIMULATION_AMENDMENT.md", "status": implementation_status, "scientific_readiness": scientific, "provisional_model": provisional_model, "code_file": "linux-simulation/src/model.py", "implemented_equations": list(meta["equations"]), "assumptions": list(meta.get("known_missing_physics", [])), "closure_blockers": list(meta.get("closure_blockers", [])), "evidence_boundary": "No new experimental or source equation claim; synthetic execution tests the code and numerical pipeline only."}
    _write_json(case_dir / "theory" / "equations.yaml", equations)
    parameter_map = _load_json(case_dir / "parameter_equation_map.yaml")
    parameter_map["implementation_update"] = {"amendment": "05_IYPT_2027_SIMULATION_AMENDMENT.md", "status": implementation_status, "package_map": "linux-simulation/parameter-map.json", "input_categories": ["controls", "geometry", "material_properties", "initial_conditions", "boundary_conditions", "calibration_parameters"], "closure_assumptions": list(meta.get("known_missing_physics", [])), "evidence_boundary": "Synthetic fixture values are not apparatus measurements."}
    _write_json(case_dir / "parameter_equation_map.yaml", parameter_map)
    handoff = _handoff(case_id, meta, mappings)
    _write_json(case_dir / "simulation_handoff.yaml", handoff)
    _write_json(case_dir / "project_state.yaml", _project_state(case_id, exact_prompt, scientific, "implementation_ready", "implementation_ready only; no execution receipt yet", "package_implemented", ["linux-simulation/simulation_package_manifest.json"]))

    # The package command creates the receipt; this script never fabricates it.
    run = subprocess.run(["bash", "run.sh"], cwd=package, text=True, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if run.returncode:
        raise RuntimeError(f"{case_id} synthetic run failed:\n{run.stdout}\n{run.stderr}")
    manifest = _load_json(package / "simulation_package_manifest.json")
    if manifest.get("software_readiness") != "runnable_synthetic":
        raise RuntimeError(f"{case_id} did not advance to runnable_synthetic")
    manifest["claim_ceiling"] = meta["claim"]
    _write_json(package / "simulation_package_manifest.json", manifest)
    handoff["highest_state"] = "runnable_synthetic"
    handoff["software_readiness"] = "runnable_synthetic"
    handoff["claim_ceiling"] = meta["claim"]
    handoff["implementation_status"] = implementation_status
    handoff["provisional_model"] = provisional_model
    _write_json(case_dir / "simulation_handoff.yaml", handoff)
    _write_json(case_dir / "project_state.yaml", _project_state(case_id, exact_prompt, scientific, "runnable_synthetic", meta["claim"], "synthetic_smoke_tested", ["linux-simulation/receipts/synthetic-smoke.json"]))


def _hold_template(case_id: str, primary_solver: str, route: str) -> dict[str, Any]:
    sections = HOLD_INPUTS[case_id]
    output: dict[str, Any] = {"case_id": case_id, "primary_solver": primary_solver, "route": route, "input_contract_version": 1, "required_input_categories": list(sections) + ["uncertainties"]}
    for category, fields in sections.items():
        output[category] = {name: {"value": None, **spec, "uncertainty_required": True} for name, spec in fields.items()}
    output["uncertainties"] = {name: {"unit": spec["unit"], "standard_uncertainty": None, "source": "required before closure"} for fields in sections.values() for name, spec in fields.items()}
    output["derived_quantities"] = {}
    output["state_variables"] = {}
    output["observables"] = {}
    output["notes"] = ["The conditional route is not activated. No solver package is generated until the closure blockers are resolved.", "Outputs and derived quantities remain outside the required input contract."]
    return output


def _hold_mappings(case_id: str, route: dict[str, Any]) -> list[dict[str, Any]]:
    equation_ids = route.get("selection_chain", {}).get("governing_equation_ids", ["closure_gate"])
    rows: list[dict[str, Any]] = []
    for category, fields in HOLD_INPUTS[case_id].items():
        for name, spec in fields.items():
            rows.append({
                "parameter": name,
                "destination_kind": "blocked conditional input",
                "destination": "closure gate record; no solver input is active",
                "equation_id": equation_ids[0],
                "implemented_file": "closure-gate record",
                "implemented_symbol": "none while held",
                "units": spec["unit"],
                "notation_conversion": "not converted; activation is blocked until closure evidence",
                "discretization_or_approximation": "not applicable before implementation",
                "implementation_assumptions": ["no implementation is authorized before the scientific closure gate is resolved"],
            })
    return rows


def _update_hold_case(case_id: str) -> None:
    case_dir = ARCHIVE / case_id
    route = _load_json(case_dir / "simulation_route.yaml")
    old_solver = route.get("primary_solver", "conditional solver")
    old_route = route.get("selected_route", "conditional route")
    route["selected_route"] = "analytical"
    route["primary_solver"] = "No numerical solver"
    route["single_solver_baseline"] = f"Conditional candidate route {old_route}/{old_solver}; not activated until the closure blockers are measured or derived without invented physics."
    route["evidence_label"] = "exploratory"
    route["rationale"] = "Solver selection is deliberately held at No numerical solver because the selected model is not closed for the requested apparatus chain."
    route["conditional_route"] = old_route
    route["conditional_solver"] = old_solver
    route["closure_gate"] = "Resolve the explicit closure blockers in solver_requirements.yaml before generating or running a solver package."
    if isinstance(route.get("selection_chain"), dict):
        route["selection_chain"]["solver"] = "No numerical solver"
        route["selection_chain"]["numerical_requirements"] = list(route["selection_chain"].get("numerical_requirements", [])) + ["closure evidence required before implementation"]
    _write_json(case_dir / "simulation_route.yaml", route)
    spec = _load_json(case_dir / "simulation_spec.yaml")
    spec["route"] = "analytical"
    spec["conditional_route"] = old_route
    spec["conditional_solver"] = old_solver
    spec["execution_boundary"] = "blocked: scientific model_selected_not_closed"
    _write_json(case_dir / "simulation_spec.yaml", spec)
    requirements = _load_json(case_dir / "solver_requirements.yaml")
    requirements["model_closure_status"] = "unresolved"
    requirements["closure_blockers"] = ["Define and measure the missing apparatus geometry/forcing/constitutive closure before solver implementation.", "Do not replace the blocker with fitted outputs or a cosmetic native case."]
    _write_json(case_dir / "solver_requirements.yaml", requirements)
    handoff = _load_json(case_dir / "simulation_handoff.yaml")
    handoff.update({"simulation_contract_version": 1, "primary_solver": "No numerical solver", "version_policy": "No solver version or native package until the closure gate is resolved.", "highest_state": "handoff_only", "scientific_readiness": "model_selected_not_closed", "software_readiness": "handoff_only", "claim_ceiling": "scientific hold; no implementation, execution, numerical verification or experimental validation claimed", "official_installation_source": "not applicable while held", "documentation_locator": "No solver package is active until solver_requirements.yaml closure_blockers are resolved."})
    handoff["parameter_mapping"] = _hold_mappings(case_id, route)
    _write_json(case_dir / "simulation_handoff.yaml", handoff)
    state = _load_json(case_dir / "project_state.yaml")
    _write_json(case_dir / "project_state.yaml", _project_state(case_id, state["exact_prompt"], "model_selected_not_closed", "handoff_only", "scientific hold; no implementation or execution claimed", "model_selected_not_closed", []))
    _write_json(case_dir / "linux-simulation" / "parameter-template.json", _hold_template(case_id, old_solver, old_route))
    _write_json(case_dir / "dependency_report.yaml", {"mode": "not_checked", "dependencies": [{"name": old_solver, "available": False, "detail": "conditional route not activated because the scientific closure gate is unresolved"}], "limitations": ["No solver package is generated while the model is not closed.", "Resolve closure blockers before dependency installation or execution."]})
    _write(case_dir / "linux-simulation" / "README.md", textwrap.dedent(f"""
        # {case_id}: simulation held at the scientific closure gate

        This continuing case is intentionally **not closed**. The previous
        conditional route was `{old_route}` with `{old_solver}`, but the archive
        does not activate a solver, generate a cosmetic case, or claim runnable
        status until the blockers in `../solver_requirements.yaml` are resolved.

        `parameter-template.json` now separates measured controls, geometry,
        material properties, initial conditions, boundary conditions, fitted
        calibration values and uncertainties. Derived quantities, states and
        observables are not required inputs.

        Beginner next step: resolve each closure blocker with a measurement or
        documented derivation, update the theory/equation lineage, then rerun
        the PT Research validator before requesting implementation.
    """).lstrip())
    _write(case_dir / "linux-simulation" / "check_system.sh", "#!/usr/bin/env bash\nset -euo pipefail\necho 'BLOCKED: scientific model_selected_not_closed; no solver package is active.' >&2\nexit 2\n", True)
    _write(case_dir / "linux-simulation" / "run_gate.sh", "#!/usr/bin/env bash\nset -euo pipefail\necho 'BLOCKED: resolve solver_requirements.yaml closure_blockers before implementation.' >&2\nexit 2\n", True)
    _write(case_dir / "linux-simulation" / "run.sh", "#!/usr/bin/env bash\nset -euo pipefail\necho 'BLOCKED: no runnable package exists while the scientific model is not closed.' >&2\nexit 2\n", True)


def _root_reports() -> None:
    rows: list[dict[str, str]] = []
    for case_id in sorted(IMPLEMENTED | PROVISIONAL | HOLDS | STOPS):
        if case_id in IMPLEMENTED:
            meta = CASE_META[case_id]
            row = {"case_id": case_id, "wave": meta["wave"], "scientific_readiness": "model_closed", "software_readiness": "runnable_synthetic", "implementation_status": "runnable_synthetic", "primary_solver": meta["solver"], "route": meta["route"], "package_status": "runnable_synthetic", "synthetic_smoke": "yes", "external_solver_check": "not run", "external_solver_execution": "not run", "claim_boundary": meta["claim"]}
        elif case_id in PROVISIONAL:
            meta = CASE_META[case_id]
            row = {"case_id": case_id, "wave": meta["wave"], "scientific_readiness": meta["scientific_readiness"], "software_readiness": "runnable_synthetic", "implementation_status": meta["implementation_status"], "primary_solver": meta["solver"], "route": meta["route"], "package_status": "runnable_provisional", "synthetic_smoke": "yes", "external_solver_check": "not run", "external_solver_execution": "not run", "claim_boundary": meta["claim"]}
        elif case_id in HOLDS:
            route = _load_json(ARCHIVE / case_id / "simulation_route.yaml")
            row = {"case_id": case_id, "wave": "Wave 3 hold", "scientific_readiness": "model_selected_not_closed", "software_readiness": "handoff_only", "implementation_status": "scientific_hold", "primary_solver": "No numerical solver", "route": route.get("selected_route", "analytical"), "package_status": "scientific_hold", "synthetic_smoke": "no", "external_solver_check": "not run", "external_solver_execution": "not run", "claim_boundary": "scientific hold; no implementation or execution claimed"}
        else:
            status = "stop_missing_data" if case_id != "14-non-newtonian-worms" else "stop_unresolved_mechanism"
            row = {"case_id": case_id, "wave": "Scientific stop", "scientific_readiness": "scientific_stop", "software_readiness": "not_applicable", "implementation_status": "scientific_stop", "primary_solver": "No numerical solver", "route": "unsupported", "package_status": "scientific_stop", "synthetic_smoke": "no", "external_solver_check": "not applicable", "external_solver_execution": "not applicable", "claim_boundary": status + "; no solver selection or package"}
        rows.append(row)
    fields = list(rows[0])
    matrix = ARCHIVE / "IYPT_2027_SIMULATION_READINESS_MATRIX.csv"
    with matrix.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    solver_matrix = ARCHIVE / "data" / "solver-prompt-matrix.csv"
    with solver_matrix.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "primary_solver", "route", "stopping_status", "report", "handoff", "scientific_readiness", "software_readiness", "implementation_status", "package_status", "external_solver_execution"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"case_id": row["case_id"], "primary_solver": row["primary_solver"], "route": row["route"], "stopping_status": "continue" if row["case_id"] not in STOPS else row["claim_boundary"].split(";")[0], "report": f"{row['case_id']}/theoretical-report.pdf", "handoff": f"{row['case_id']}/linux-simulation", "scientific_readiness": row["scientific_readiness"], "software_readiness": row["software_readiness"], "implementation_status": row["implementation_status"], "package_status": row["package_status"], "external_solver_execution": row["external_solver_execution"]})
    _write(ARCHIVE / "RUNNABLE_SIMULATION_CHANGELOG.md", textwrap.dedent("""
        # IYPT 2027 runnable-simulation implementation changelog

        Date: 2026-08-07. Instruction basis: `05_IYPT_2027_SIMULATION_AMENDMENT.md`.

        ## Theory and model state

        - 03 Snail ball, 13 Vortex pendulum and 14 Non-Newtonian worms remain justified scientific stops.
        - 05 Y-shaped pendulum, 07 Sinking funnel, 11 Sound isolation and 16 Magnetic carousel remain `model_selected_not_closed` scientifically, but now have `runnable_provisional` synthetic implementations under Amendment 05.
        - 12 Dotted line trick and 15 Cold drink now use the required Python/SciPy route labels. Their calibrated visibility and freezing-curve closures are implemented as package inputs/outputs without claiming external execution.

        ## Schema and implementation

        - Every continuing case has an explicit input template separating measured controls, geometry, material properties, initial conditions, boundary conditions, fitted calibration values and uncertainties.
        - The four amended Wave 3 cases contain case-specific source code, reduced and/or replaceable closure functions, extraction, state-aware gates, synthetic examples, native route assets, parameter maps, equation-lineage updates and three-level numerical-verification plans.
        - `runnable_synthetic` means the package command produced finite machine-readable output and a receipt. It does not mean the selected external solver ran.

        ## Numerical and experimental results

        - The synthetic smoke receipts are real command receipts generated by each package's `run.sh`.
        - No HCIPy, Elmer FEM, OpenFOAM, Project Chrono or SciPy external production run is claimed by this archive.
        - `numerical-verification.json` remains `unexecuted` for every generated package; experimental comparison remains unexecuted.
    """).lstrip())
    _write(ARCHIVE / "RUNNABLE_SIMULATION_UBUNTU_GUIDE.md", textwrap.dedent("""
        # Beginner Ubuntu guide: IYPT 2027 simulation archive

        1. Enter a case package, for example `cd 01-pinhole-sunglasses/linux-simulation`.
        2. Run `bash check_system.sh --mode synthetic`.
        3. Run `bash run_gate.sh` and then `bash run.sh`.
        4. Inspect `outputs/results.json` and `receipts/synthetic-smoke.json`.
        5. Run `python3 tests/test_synthetic.py` and `python3 tests/test_route_contract.py`.

        The synthetic path uses the Python standard library. External solver
        installation is deliberately separate: review `requirements.txt`,
        `environment.yml`, the case-root `dependency_report.yaml` and the
        official solver documentation before installing anything. Fill
        `examples/apparatus-template.json` only with measured values, field-level
        provenance and uncertainties. Apparatus mode is state-gated and does
        not itself establish experimental validity.

        Cases marked `scientific_stop` have no active runnable package. The
        four `runnable_provisional` cases may be smoke-tested, but their
        documented closure gates still block apparatus and predictive claims.
    """).lstrip())
    _write(ARCHIVE / "RUNNABLE_SIMULATION_EXECUTED_LIST.md", "# Executed list\n\nSynthetic package smoke commands executed: " + ", ".join(sorted(IMPLEMENTED | PROVISIONAL)) + ".\n\nExternal solver production executions: none.\n")
    _write(ARCHIVE / "RUNNABLE_SIMULATION_NOT_EXECUTED_LIST.md", "# Not executed\n\nExternal solver runs, three-level numerical verification and experimental comparisons: none for all 17 cases.\n")
    _write(ARCHIVE / "RUNNABLE_SIMULATION_STOPPED_OR_NOT_CLOSED.md", "# Stopped or not closed\n\n- Scientific stops: 03 Snail ball, 13 Vortex pendulum, 14 Non-Newtonian worms.\n- Provisional implementations with unresolved closure: 05 Y-shaped pendulum, 07 Sinking funnel, 11 Sound isolation, 16 Magnetic carousel.\n\nThe provisional cases have runnable synthetic code but no apparatus, predictive, numerical-verification or experimental-validation claim.\n")


def main() -> int:
    global ARCHIVE
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    ARCHIVE = args.archive.resolve()
    generic = _import_generic_generator()
    for case_id in sorted(IMPLEMENTED | PROVISIONAL):
        _update_implemented_case(case_id, generic)
    for case_id in sorted(HOLDS):
        _update_hold_case(case_id)
    _root_reports()
    print(f"updated {len(IMPLEMENTED)} closed runnable packages, {len(PROVISIONAL)} provisional runnable packages, {len(HOLDS)} scientific holds, and {len(STOPS)} scientific stops")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
