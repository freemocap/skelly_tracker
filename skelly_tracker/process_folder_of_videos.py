import logging
from multiprocessing import Pool, cpu_count
from pathlib import Path
import sys
from typing import Any, Optional, Type
import numpy as np
from pydantic import BaseModel


from skelly_tracker.trackers.base_tracker.base_tracker import BaseTracker
from skelly_tracker.trackers.bright_point_tracker.brightest_point_tracker import (
    BrightestPointTracker,
)
from skelly_tracker.trackers.mediapipe_tracker.mediapipe_holistic_tracker import (
    MediapipeHolisticTracker,
)
from skelly_tracker.trackers.yolo_mediapipe_combo_tracker.yolo_mediapipe_combo_tracker import (
    YOLOMediapipeComboTracker,
)
from skelly_tracker.trackers.yolo_tracker.yolo_tracker import YOLOPoseTracker
from skelly_tracker.trackers.mediapipe_tracker.mediapipe_model_info import (
    MediapipeTrackingParams,
)

logger = logging.getLogger(__name__)

file_name_dictionary = {
    "MediapipeHolisticTracker": "mediapipe2dData_numCams_numFrames_numTrackedPoints_pixelXY.npy",
    "YOLOMediapipeComboTracker": "mediapipe2dData_numCams_numFrames_numTrackedPoints_pixelXY.npy",
    "YOLOPoseTracker": "yolo2dData_numCams_numFrames_numTrackedPoints_pixelXY.npy",
    "BrightestPointTracker": "brightestPoint2dData_numCams_numFrames_numTrackedPoints_pixelXY.npy",
}


def process_folder_of_videos(
    tracker_name: str,
    tracking_params: BaseModel,
    synchronized_video_path: Path,
    output_path: Optional[Path] = None,
    annotated_video_path: Optional[Path] = None,
    num_processes: int = None,
) -> None:
    """
    Process a folder of synchronized videos with the given tracker.
    Tracked data will be saved to a .npy file with the shape (numCams, numFrames, numTrackedPoints, pixelXYZ).

    :param tracker_name: Tracker to use.
    :param tracking_params: Tracking parameters to use.
    :param synchronized_video_path: Path to folder of synchronized videos.
    :param output_path: Path to save tracked data to.
    :param annotated_video_path: Path to save annotated videos to.
    :param num_processes: Number of processes to use, 1 to disable multiprocessing.
    :return: Array of tracking data
    """
    if num_processes is None:
        num_processes = min(
            (cpu_count() - 1), len(list(synchronized_video_path.glob("*.mp4")))
        )

    file_name = file_name_dictionary[tracker_name]
    synchronized_video_path = Path(synchronized_video_path)
    if output_path is None:
        output_path = (
            synchronized_video_path.parent / "output_data" / "raw_data" / file_name
        )
    if not output_path.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if annotated_video_path is None:
        annotated_video_path = synchronized_video_path.parent / "annotated_videos"
    if not annotated_video_path.exists():
        annotated_video_path.mkdir(parents=True, exist_ok=True)

    tasks = [
        (tracker_name, tracking_params, video_path, annotated_video_path)
        for video_path in synchronized_video_path.glob("*.mp4")
    ]

    if num_processes > 1:
        logging.info("Using multiprocessing to run pose estimation")
        with Pool(processes=num_processes) as pool:
            array_list = pool.starmap(process_single_video, tasks)
    else:
        array_list = []
        for task in tasks:
            array_list.append(process_single_video(*task))

    combined_array = np.stack(array_list)

    logger.info(f"Shape of output array: {combined_array.shape}")
    np.save(output_path, combined_array)

    return combined_array


def process_single_video(
    tracker_name: str,
    tracking_params: BaseModel,
    video_path: Path,
    annotated_video_path: Path,
) -> np.ndarray:
    """
    Process a single video with the given tracker.
    Tracked data will be saved to a .npy file with the shape (numCams, numFrames, numTrackedPoints, pixelXYZ).

    :param tracker_name: Tracker to use.
    :param tracking_params: Tracking parameters to use.
    :param video_path: Path to video.
    :param annotated_video_path: Path to save annotated video to.
    :return: Array of tracking data
    """
    video_name = (
        video_path.stem + "_mediapipe.mp4"
    )  # TODO: fix it so blender output doesn't require mediapipe addendum here
    tracker = get_tracker(tracker_name=tracker_name, tracking_params=tracking_params)
    logger.info(
        f"Processing video: {video_name} with tracker: {tracker.__class__.__name__}"
    )
    output_array = tracker.process_video(
        input_video_filepath=video_path,
        output_video_filepath=annotated_video_path / video_name,
        save_data_bool=False,
    )
    tracker.recorder.clear_recorded_objects()
    return output_array


def get_tracker(tracker_name: str, tracking_params: BaseModel) -> BaseTracker:
    """
    Returns a tracker object based on the given tracker_type and tracking_params.

    :param tracker_type (str): The type of tracker to be created.
    :param tracking_params (BaseModel): The tracking parameters to be used for creating the tracker.
    :return BaseTracker: The tracker object based on the given tracker_type and tracking_params.
    :raise ValueError: If an invalid tracker_type is provided.
    """
    match tracker_name:
        case "MediapipeHolisticTracker":
            tracker = MediapipeHolisticTracker(
                model_complexity=tracking_params.mediapipe_model_complexity,
                min_detection_confidence=tracking_params.min_detection_confidence,
                min_tracking_confidence=tracking_params.min_tracking_confidence,
                static_image_mode=tracking_params.static_image_mode,
            )

        case "YOLOMediapipeComboTracker":
            tracker = YOLOMediapipeComboTracker(
                model_complexity=tracking_params.mediapipe_model_complexity,
                min_detection_confidence=tracking_params.min_detection_confidence,
                min_tracking_confidence=tracking_params.min_tracking_confidence,
                static_image_mode=True,  # yolo cropping must be run with static image mode due to changing size of bounding boxes
            )

        case "YOLOPoseTracker":
            tracker = YOLOPoseTracker(
                model_size="medium",
            )

        case "BrightestPointTracker":
            tracker = BrightestPointTracker()

        case _:
            raise ValueError("Invalid tracker type")

    return tracker


if __name__ == "__main__":
    synchronized_video_path = Path(
        "/Users/philipqueen/freemocap_data/recording_sessions/freemocap_sample_data/synchronized_videos"
    )
    tracker_name = "YOLOMediapipeComboTracker"
    num_processes = None

    process_folder_of_videos(
        tracker_name=tracker_name,
        tracking_params=MediapipeTrackingParams(),
        synchronized_video_path=synchronized_video_path,
        num_processes=num_processes,
    )
