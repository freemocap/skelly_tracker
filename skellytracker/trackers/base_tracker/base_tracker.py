import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import numpy as np
import cv2

from skellytracker.trackers.demo_viewers.image_demo_viewer import ImageDemoViewer
from skellytracker.trackers.demo_viewers.webcam_demo_viewer import (
    WebcamDemoViewer,
)

logger = logging.getLogger(__name__)

TrackedPointId = str

@dataclass
class BaseObservation(ABC):

    @classmethod
    @abstractmethod
    def from_detection_results(cls, *args, **kwargs):
        pass

    @abstractmethod
    def to_serializable_dict(self) -> dict:
        pass

    def to_json_string(self) -> str:
        return json.dumps(self.to_serializable_dict(), indent=4)

    def to_json_bytes(self) -> bytes:
        return self.to_json_string().encode("utf-8")

BaseObservations = list[BaseObservation]

@dataclass
class BaseImageAnnotatorConfig(ABC):
    pass


@dataclass
class BaseImageAnnotator(ABC):
    config: BaseImageAnnotatorConfig
    observations: BaseObservations = field(default_factory=list) #for plotting trails, etc.

    @classmethod
    def create(cls, config: BaseImageAnnotatorConfig):
        raise NotImplementedError("Must implement a method to create an image annotator from a config.")

    @abstractmethod
    def annotate_image(self, image: np.ndarray, latest_observation: BaseObservation) -> np.ndarray:
        pass

    @staticmethod
    def draw_doubled_text(image: np.ndarray,
                          text: str,
                          x: int,
                          y: int,
                          font_scale: float,
                          color: tuple[int, int, int],
                          thickness:int):
        cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness * 2)
        cv2.putText(image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)

@dataclass
class BaseDetectorConfig(ABC):
    pass

@dataclass
class BaseTrackerConfig(ABC):
    detector_config: BaseDetectorConfig
    annotator_config: BaseImageAnnotatorConfig | None = None

@dataclass
class BaseDetector(ABC):
    config: BaseDetectorConfig

    @classmethod
    def create(cls, config: BaseDetectorConfig):
        raise NotImplementedError("Must implement a method to create a detector from a config.")

    @abstractmethod
    def detect(self, image: np.ndarray) -> BaseObservation:
        pass


@dataclass
class BaseRecorder(ABC):
    observations: List[BaseObservation] = field(default_factory=list)

    def add_observations(self, observation: BaseObservation):
        self.observations.append(observation)


@dataclass
class BaseObservationManager(ABC):
    observations: List[BaseObservation] = field(default_factory=list)
    @abstractmethod
    def create_observation(self, **kwargs) -> BaseObservation:
        pass


@dataclass
class BaseTracker(ABC):
    config: BaseTrackerConfig
    detector: BaseDetector

    annotator: BaseImageAnnotator | None = None

    @classmethod
    def create(cls, config: BaseTrackerConfig):
        raise NotImplementedError("Must implement a method to create a tracker from a config.")

    def process_image(self, image: np.ndarray, annotate_image: bool = False) -> tuple[np.ndarray, BaseObservation]|BaseObservation:
        latest_observation = self.detector.detect(image)
        if annotate_image:
            return self.annotator.annotate_image(image=image, latest_observation=latest_observation), latest_observation
        return latest_observation


    def demo(self) -> None:
        camera_viewer = WebcamDemoViewer(
            tracker=self,
            window_title=self.__class__.__name__
        )
        camera_viewer.run()

    def image_demo(self, image_path: Path) -> None:
        """
        Run tracker on single image

        :return: None
        """

        image_viewer = ImageDemoViewer(self, self.__class__.__name__)
        image_viewer.run(image_path=image_path)

    # def process_video(
    #         self,
    #         input_video_filepath: str,
    #         output_data_directory: str,
    #         output_video_filepath: str | None = None,
    #         use_tqdm: bool = True,
    # ):
    #     """
    #     Run the tracker on a video.
    #
    #     :param input_video_filepath: Path to video file.
    #     :param output_data_directory: Path to save the data to.
    #     :param output_video_filepath: Path to save annotated video to, does not save video if None.
    #     :param use_tqdm: Whether to use tqdm to show a progress bar
    #     """
    #
    #     cap = cv2.VideoCapture(str(input_video_filepath))
    #
    #     width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    #     height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    #     image_size = (width, height)
    #
    #     fps = cap.get(cv2.CAP_PROP_FPS)
    #
    #     if output_video_filepath is not None:
    #         video_handler = VideoHandler(
    #             output_path=output_video_filepath, frame_size=image_size, fps=fps
    #         )
    #     else:
    #         video_handler = None
    #
    #     ret, frame = cap.read()
    #
    #     number_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    #
    #     if use_tqdm:
    #         iterator = tqdm(
    #             range(number_of_frames),
    #             desc=f"processing video: {Path(input_video_filepath).name}",
    #             total=number_of_frames,
    #             color="magenta",
    #             unit="frames",
    #             dynamic_ncols=True,
    #         )
    #     else:
    #         iterator = range(number_of_frames)
    #
    #     for _frame_number in iterator:
    #         if not ret or frame is None:
    #             logger.error(
    #                 f"Failed to load an image from: {str(input_video_filepath)}"
    #             )
    #             raise ValueError("Failed to load an image from: " + str(input_video_filepath))
    #
    #         self.process_image(frame)
    #         if self.recorder is not None:
    #             self.recorder.record(self.tracked_objects)
    #         if video_handler is not None:
    #             if self.annotated_image is None:
    #                 self.annotated_image = frame
    #             video_handler.add_frame(self.annotated_image)
    #
    #         ret, frame = cap.read()
    #
    #     cap.release()
    #     if video_handler is not None:
    #         video_handler.close()
    #
    #     output_array = self.process_and_save_tracked_objects(
    #         input_video_filepath,  image_size
    #     )
    #
    #     self.cleanup()
    #
    #     return output_array
    #
    # def process_and_save_tracked_objects(
    #         self,
    #         input_video_filepath: Union[str, Path],
    #         save_data_bool: bool,
    #         image_size: tuple,
    # ) -> Optional[np.ndarray]:
    #     if self.recorder is not None:
    #         output_array = self.recorder.process_tracked_objects(image_size=image_size)
    #         if save_data_bool:
    #             self.recorder.save(
    #                 file_path=str(Path(input_video_filepath).with_suffix(".npy"))
    #             )
    #     else:
    #         output_array = None
    #     return output_array
    #
    # def cleanup(self) -> None:
    #     """
    #     Run any cleanup code for the tracker, including clearing the recorded objects.
    #
    #     Can be overridden by subclasses if any tracker needs a specific cleanup.
    #     """
    #     if self.recorder is not None:
    #         self.recorder.clear_recorded_objects()

    #
    #
#
# class BaseCumulativeTracker(BaseTracker):
#     """
#     A base class for tracking algorithms that run cumulatively, i.e are not able to process videos frame by frame.
#     Throws a descriptive error for the abstract methods of BaseTracker that do not apply to this type of tracker.
#     Trackers inheriting from this will need to overwrite the `process_video` method.
#     """
#
#     def __init__(
#             self,
#             tracked_object_names: List[str],
#             recorder: BaseCumulativeRecorder,
#             **data: Any,
#     ):
#         super().__init__(
#             tracked_object_names=tracked_object_names, recorder=recorder, **data
#         )
#
#     def process_image(self, **kwargs) -> None:
#         raise NotImplementedError(
#             "This tracker does not support processing individual images, please use process_video instead."
#         )
#
#     def annotate_image(self, **kwargs) -> None:
#         raise NotImplementedError(
#             "This tracker does not support processing individual images, please use process_video instead."
#         )
#
#     @abstractmethod
#     def process_video(
#             self,
#             input_video_filepath: Union[str, Path],
#             output_video_filepath: Optional[Union[str, Path]] = None,
#             save_data_bool: bool = False,
#             use_tqdm: bool = True,
#             **kwargs,
#     ) -> Union[np.ndarray, None]:
#         """
#         Run the tracker on a video.
#
#         :param input_video_filepath: Path to video file.
#         :param output_video_filepath: Path to save annotated video to, does not save video if None.
#         :param save_data_bool: Whether to save the data to a file.
#         :param use_tqdm: Whether to use tqdm to show a progress bar
#         :return: Array of tracked keypoint data
#         """
#         pass
#
#     def image_demo(self, image_path: Path) -> None:
#         raise NotImplementedError(
#             "This tracker does not support processing individual images, please use process_video instead."
#         )
