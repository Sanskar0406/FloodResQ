import math
from typing import List, Optional, Tuple, Dict, Any

EARTH_RADIUS_KM = 6371.0

def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two GPS coordinates in kilometers."""
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c

def find_nearest_resource(
    report_lat: Optional[float],
    report_lng: Optional[float],
    need_type: str,
    resources: List[Any]
) -> Optional[Dict[str, Any]]:
    """
    Find nearest available resource matching need_type.
    If no exact match by type is available, finds nearest available rescue resource.
    """
    if report_lat is None or report_lng is None or not resources:
        return None

    # First attempt: match exact need_type
    candidates = [
        r for r in resources
        if r.available and r.type == need_type and r.lat is not None and r.lng is not None
    ]

    # Fallback: if no exact matching type is available, look for rescue or any available resource
    if not candidates:
        candidates = [
            r for r in resources
            if r.available and r.lat is not None and r.lng is not None
        ]

    if not candidates:
        return None

    best = None
    min_dist = float("inf")

    for res in candidates:
        dist = haversine_km(report_lat, report_lng, res.lat, res.lng)
        if dist < min_dist:
            min_dist = dist
            best = res

    if best:
        return {
            "resource": best.to_dict() if hasattr(best, "to_dict") else best,
            "distance_km": round(min_dist, 2),
            "eta_minutes": max(3, int(min_dist * 4 + 2))  # Rough estimate based on traffic/water navigation
        }
    return None
