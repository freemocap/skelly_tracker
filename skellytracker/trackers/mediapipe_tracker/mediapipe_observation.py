import json
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
from mediapipe.python.solutions import holistic as mp_holistic
from mediapipe.python.solutions.face_mesh import FACEMESH_NUM_LANDMARKS_WITH_IRISES
from mediapipe.framework.formats.landmark_pb2 import NormalizedLandmarkList

from skellytracker.trackers.base_tracker.base_tracker import BaseObservation


@dataclass
class MediapipeObservation(BaseObservation):
    pose_landmarks: NormalizedLandmarkList
    right_hand_landmarks: NormalizedLandmarkList
    left_hand_landmarks: NormalizedLandmarkList
    face_landmarks: NormalizedLandmarkList

    image_size: tuple[int, int]

    @classmethod
    def from_detection_results(cls,
                                  mediapipe_results: NamedTuple,
                                  image_size: tuple[int, int]):
        return cls(
            pose_landmarks=mediapipe_results.pose_landmarks,
            right_hand_landmarks=mediapipe_results.right_hand_landmarks,
            left_hand_landmarks=mediapipe_results.left_hand_landmarks,
            face_landmarks=mediapipe_results.face_landmarks,
            image_size=image_size
        )

    @property
    def pose_landmarks_empty(self):
        return self.pose_landmarks is None  # TODO: check if these are ever None, or empty lists, or always have values

    @property
    def right_hand_landmarks_empty(self):
        return self.right_hand_landmarks is None

    @property
    def left_hand_landmarks_empty(self):
        return self.left_hand_landmarks is None

    @property
    def face_landmarks_empty(self):
        return self.face_landmarks is None

    @property
    def body_landmark_names(self) -> list[str]:
        return [landmark.name.lower() for landmark in mp_holistic.PoseLandmark]

    @property
    def hand_landmark_names(self) -> list[str]:
        return [landmark.name.lower() for landmark in mp_holistic.HandLandmark]

    @property
    def num_body_points(self) -> int:
        return len(self.body_landmark_names)

    @property
    def num_single_hand_points(self) -> int:
        return len(self.hand_landmark_names)

    @property
    def num_face_points(self) -> int:
        return FACEMESH_NUM_LANDMARKS_WITH_IRISES

    @property
    def num_total_points(self) -> int:
        return self.num_body_points + (2 * self.num_single_hand_points) + self.num_face_points

    @property
    def pose_trajectories(self) -> np.ndarray[..., 3]:  # TODO: not sure how to type these array sizes, seems like it doesn't like the `self` reference
        if self.pose_landmarks_empty:
            return np.full((self.num_body_points, 3), np.nan)

        return self.landmarks_to_array(self.pose_landmarks)

    @property
    def right_hand_trajectories(self) -> np.ndarray[..., 3]:
        if self.right_hand_landmarks_empty:
            return np.full((self.num_single_hand_points, 3), np.nan)

        return self.landmarks_to_array(self.right_hand_landmarks)

    @property
    def left_hand_trajectories(self) -> np.ndarray[..., 3]:
        if self.left_hand_landmarks_empty:
            return np.full((self.num_single_hand_points, 3), np.nan)

        return self.landmarks_to_array(self.left_hand_landmarks)

    @property
    def face_trajectories(self) -> np.ndarray[..., 3]:
        if self.face_landmarks_empty:
            return np.full((self.num_face_points, 3), np.nan)

        return self.landmarks_to_array(self.face_landmarks)

    @property
    def all_holistic_trajectories(self) -> np.ndarray[533, 3]:
        return np.concatenate(
            # this order matters, do not change
            (
                self.pose_trajectories,
                self.right_hand_trajectories,
                self.left_hand_trajectories,
                self.face_trajectories,
            ),
            axis=0,
        )

    def landmarks_to_array(self, landmarks: NormalizedLandmarkList) -> np.ndarray[..., 3]:
        landmark_array = np.array(
            [
                (landmark.x, landmark.y, landmark.z)
                for landmark in landmarks.landmark
            ]
        )

        # convert from normalized image coordinates to pixel coordinates
        landmark_array *= np.array([self.image_size[0], self.image_size[1], self.image_size[0]])  # multiply z by image width per mediapipe docs

        return landmark_array

    def to_serializable_dict(self) -> dict:
        d =  {
            "pose_trajectories": self.pose_trajectories.tolist(),
            "right_hand_trajectories": self.right_hand_trajectories.tolist(),
            "left_hand_trajectories": self.left_hand_trajectories.tolist(),
            "face_trajectories": self.face_trajectories.tolist(),
            "image_size": self.image_size
        }
        try:
            json.dumps(d).encode("utf-8")
        except Exception as e:
            raise ValueError(f"Failed to serialize MediapipeObservation to JSON: {e}")
        return d

MediapipeObservations = list[MediapipeObservation]
