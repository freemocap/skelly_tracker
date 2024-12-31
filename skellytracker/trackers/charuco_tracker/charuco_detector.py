from dataclasses import dataclass
from typing import List

import cv2
import numpy as np

from skellytracker.trackers.base_tracker.base_tracker import BaseDetectorConfig, BaseDetector
from skellytracker.trackers.charuco_tracker.charuco_observations import CharucoObservation, CharucoObservationFactory

DEFAULT_ARUCO_DICTIONARY = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)

class CharucoDetectorConfig(BaseDetectorConfig):
    squares_x: int = 5
    squares_y: int = 3
    aruco_dictionary: cv2.aruco.Dictionary = DEFAULT_ARUCO_DICTIONARY
    square_length: float = 1
    marker_length: float = 0.8

    @property
    def charuco_corner_ids(self) -> List[int]:
        return list(range((self.squares_x - 1) * (self.squares_y - 1)))

    @property
    def charuco_corners_in_object_coordinates(self) -> List[np.ndarray]:
        """
        Returns the corners of the Charuco board in object coordinates,
        where the z coordinate is 0 for all corners.
        so, for a 5x3 board, this would return a list of 8 corners, each with a shape of (8, 3), e.g.:
        [[0,0,0],
        [0,1,0],
        [1,0,0],
        [1,1,0],
        [2,0,0],
        [2,1,0],
        [0,3,0],
        [1,3,0]]
        """
        return [np.array([[x, y, 0] for x in range(self.squares_x - 1) for y in range(self.squares_y - 1)])]


@dataclass
class CharucoDetector(BaseDetector):
    config: CharucoDetectorConfig
    board: cv2.aruco.CharucoBoard
    detector: cv2.aruco.CharucoDetector
    observation_factory: CharucoObservationFactory

    @classmethod
    def create(cls, config: CharucoDetectorConfig):
        board = cv2.aruco.CharucoBoard(
            size=(config.squares_x, config.squares_y),
            squareLength=config.square_length,
            markerLength=config.marker_length,
            dictionary=config.aruco_dictionary,
        )
        detector = cv2.aruco.CharucoDetector(board)
        return cls(
            config=config,
            board=board,
            detector=detector,
            observation_factory=CharucoObservationFactory(charuco_corner_ids=config.charuco_corner_ids,
                                                          aruco_marker_ids=list(board.getIds()),
                                                          charuco_corner_object_coordinates=config.charuco_corners_in_object_coordinates),
        )

    @property
    def aruco_marker_ids(self) -> List[int]:
        return list(self.board.getIds())

    @property
    def board_object_points(self) -> List[np.ndarray]:
        return list(self.board.getObjPoints())  # type: ignore

    def detect(self, image: np.ndarray) -> CharucoObservation:
        if len(image.shape) == 2:
            grey_image = image
        else:
            grey_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return self.observation_factory.create_observation(*self.detector.detectBoard(grey_image),
                                                           image_size=image.shape[:2])
