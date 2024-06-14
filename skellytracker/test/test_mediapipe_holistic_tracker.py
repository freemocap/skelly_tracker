import math
import cv2
import pytest
import numpy as np


from skellytracker.trackers.mediapipe_tracker.mediapipe_model_info import (
    MediapipeModelInfo,
)
from skellytracker.trackers.mediapipe_tracker.mediapipe_holistic_tracker import (
    MediapipeHolisticTracker,
)


@pytest.mark.usefixtures("test_image")
def test_process_image(test_image):
    tracker = MediapipeHolisticTracker(model_complexity=0)
    tracked_objects = tracker.process_image(test_image)

    assert len(tracked_objects) == 4
    assert tracked_objects["pose_landmarks"] is not None
    assert tracked_objects["pose_landmarks"].extra["landmarks"] is not None
    assert tracked_objects["right_hand_landmarks"] is not None
    assert tracked_objects["right_hand_landmarks"].extra["landmarks"] is not None
    assert tracked_objects["left_hand_landmarks"] is not None
    assert tracked_objects["left_hand_landmarks"].extra["landmarks"] is not None
    assert tracked_objects["face_landmarks"] is not None
    assert tracked_objects["face_landmarks"].extra["landmarks"] is not None


@pytest.mark.usefixtures("test_image")
def test_annotate_image(test_image):
    tracker = MediapipeHolisticTracker(model_complexity=0)
    tracker.process_image(test_image)

    assert tracker.annotated_image is not None


@pytest.mark.usefixtures("test_image")
def test_record(test_image):
    tracker = MediapipeHolisticTracker(model_complexity=0)
    tracked_objects = tracker.process_image(test_image)
    tracker.recorder.record(tracked_objects=tracked_objects)
    assert len(tracker.recorder.recorded_objects) == 1
    assert len(tracker.recorder.recorded_objects[0]) == 4

    processed_results = tracker.recorder.process_tracked_objects(
        image_size=test_image.shape[:2]
    )
    assert processed_results is not None
    assert processed_results.shape == (
        1,
        MediapipeModelInfo.num_tracked_points_total,
        3,
    )

    expected_results = np.array(
        [
            [
                [724.9490356445312, 80.74257552623749, -993.9854431152344],
                [748.7973022460938, 76.24467730522156, -955.4129028320312],
                [757.65625, 77.80313193798065, -955.689697265625],
                [765.3969573974609, 79.39812362194061, -955.8861541748047],
                [724.6346282958984, 73.26869666576385, -956.6817474365234],
                [717.9697418212891, 72.75395393371582, -956.7975616455078],
                [711.0582733154297, 72.3196667432785, -956.7622375488281],
                [775.3928375244141, 86.46261692047119, -668.9157867431641],
                [700.8257293701172, 76.53615295886993, -673.5513305664062],
                [736.4148712158203, 91.9196355342865, -881.9746398925781],
                [704.9551391601562, 87.58252501487732, -883.7062072753906],
                [822.0133209228516, 152.90948510169983, -438.8511276245117],
                [543.9170837402344, 128.66411805152893, -474.09820556640625],
                [830.2363586425781, 222.54773139953613, -348.53546142578125],
                [391.7664337158203, 185.8674716949463, -379.22679901123047],
                [850.4001617431641, 281.42955780029297, -597.9225921630859],
                [251.3930320739746, 234.69798803329468, -603.9112854003906],
                [856.3973236083984, 297.1209526062012, -668.1196594238281],
                [213.4073257446289, 246.7552900314331, -670.8364105224609],
                [846.2405395507812, 297.8205370903015, -768.86962890625],
                [218.36742401123047, 250.46862602233887, -770.2429962158203],
                [841.2351226806641, 292.3808026313782, -645.0504302978516],
                [237.8342628479004, 244.97743606567383, -649.0667724609375],
                [642.2610473632812, 267.2499203681946, 19.359580278396606],
                [489.5075225830078, 252.38561153411865, -18.99002432823181],
                [545.5322647094727, 353.45691204071045, 95.11228561401367],
                [421.98192596435547, 343.2889795303345, -111.5739917755127],
                [483.64437103271484, 413.63812923431396, 892.3109436035156],
                [386.21551513671875, 410.32382011413574, 586.4739990234375],
                [469.1791534423828, 416.32561683654785, 958.9944458007812],
                [386.70398712158203, 417.09611892700195, 642.3279571533203],
                [473.2674789428711, 447.85693645477295, 729.4257354736328],
                [355.9325408935547, 444.5236587524414, 379.90428924560547],
                [253.68976593017578, 234.29851055145264, 0.0001452891228836961],
                [240.58324813842773, 234.31915283203125, -17.537919282913208],
                [225.88279724121094, 236.56160831451416, -26.281862258911133],
                [216.74800872802734, 239.36949491500854, -33.34794282913208],
                [207.5124740600586, 241.5495729446411, -39.871764183044434],
                [203.52766036987305, 250.0307822227478, -13.84335994720459],
                [184.57786560058594, 257.0957851409912, -22.172749042510986],
                [172.95087814331055, 261.3565707206726, -29.567382335662842],
                [163.63656997680664, 264.60676431655884, -34.58906173706055],
                [210.67567825317383, 252.71584510803223, -10.44108510017395],
                [192.9056167602539, 260.5885577201843, -17.135307788848877],
                [181.97023391723633, 265.8717155456543, -23.215365409851074],
                [173.35857391357422, 269.7653818130493, -27.345290184020996],
                [219.38091278076172, 253.6610770225525, -8.99298369884491],
                [204.17118072509766, 261.2510418891907, -14.699053764343262],
                [195.27652740478516, 266.1923360824585, -19.270341396331787],
                [187.59790420532227, 269.8603105545044, -22.399024963378906],
                [230.7835578918457, 253.28086853027344, -9.420499801635742],
                [223.0868148803711, 259.03817653656006, -14.548875093460083],
                [218.3838653564453, 262.8340816497803, -17.04281210899353],
                [214.09095764160156, 265.90606927871704, -18.470606803894043],
                [831.3526916503906, 290.13811111450195, 0.00027009031327906996],
                [834.6914672851562, 290.1472735404968, -28.73823642730713],
                [838.1427764892578, 291.96690559387207, -45.007004737854004],
                [837.1710205078125, 295.0093674659729, -56.84781551361084],
                [838.1177520751953, 298.5115385055542, -67.84458637237549],
                [836.1019134521484, 307.75739192962646, -34.55303907394409],
                [831.5267944335938, 317.115318775177, -48.21352005004883],
            ]
        ]
    )
    assert np.allclose(
        processed_results[:, :60, :], expected_results[:, :60, :], atol=1e-2
    )
