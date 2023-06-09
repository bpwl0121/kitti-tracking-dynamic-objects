import find_moving_object as fmo
import cv2
import os
import numpy as np
import data_association as da
import sys
sys.path.append("..")


def generate_video_from_image_seq(image_folder, video_file_path):
    """generate video from image sequence for better visualization
    Args:
        image_folder: the folder that contains all the images
        video_file_path: the path of the output video
    """
    # the fps of the video
    fps = 10

    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()

    frame = cv2.imread(os.path.join(image_folder, images[0]))
    height, width, layers = frame.shape

    out = cv2.VideoWriter(video_file_path, cv2.VideoWriter_fourcc(
        *'H264'), fps, (width, height))

    for filename in images:

        img = cv2.imread(os.path.join(image_folder, filename))
        out.write(img)

    out.release()


def save_moving_bbox_image(sequence_num, idx, all_obj_info_dict, all_moving_id_dict):
    """save the image with moving object bbox

    """
    img_path = os.path.join(
        "data_tracking_image_2/training/image_02/", sequence_num, f"{(idx):06d}.png")
    output_path = os.path.join(
        "all_bbox_img", sequence_num, f"{(idx):06d}.png")
    img = cv2.imread(img_path)
    if idx not in all_obj_info_dict[sequence_num]:
        print("the frame {} of sequence {} do not have any label at all, even static object.".format(
            idx, sequence_num))
    else:
        for obj_id, obj_info in all_obj_info_dict[sequence_num][idx].items():
            if obj_id not in all_moving_id_dict[sequence_num][idx]:
                continue
            bbox_2d = obj_info[1]
            left_top = int(bbox_2d[0]), int(bbox_2d[1])
            right_bottom = int(bbox_2d[2]), int(bbox_2d[3])
            cv2.rectangle(img, left_top, right_bottom, (0, 255, 0), 7)
    cv2.imwrite(output_path, img)


def save_seqs_moving_bbox_image(moving_threshold):
    """save the image with moving object bbox for all the sequences
    Args:
        moving_threshold: the threshold to determine whether the object is moving or not  
    """
    fulltrain = r"fulltrain.seqmap"
    seqmap, max_frames = fmo.SeqmapLoader.load_seqmap(fulltrain)
    label_folder = r"data_tracking_label_2/training/label_02"
    pose_folder = r"orbslam3_poses"
    all_obj_info_dict, all_moving_id_dict = fmo.MovingObjectDetector.find_all_moving_obj_id(
        label_folder, pose_folder, seqmap, moving_threshold)
    for seq_num, frame_nums in max_frames.items():
        os.makedirs(os.path.join("all_bbox_img", seq_num), exist_ok=True)
        for frame_num in range(frame_nums+1):
            save_moving_bbox_image(
                seq_num, frame_num, all_obj_info_dict, all_moving_id_dict)


def generate_all_videos_from_bbox_image():
    """generate all the videos from the bbox images
    """
    image_root_folder = "all_bbox_img"
    fulltrain = r"fulltrain.seqmap"
    all_seq, _ = fmo.SeqmapLoader.load_seqmap(fulltrain)
    for seq in all_seq:
        curr_image_folder = os.path.join(image_root_folder, seq)
        # new the folder first!!!!!!!!!!!!!!!!!
        output_path = os.path.join("all_videos", seq+".mp4")
        generate_video_from_image_seq(curr_image_folder, output_path)


def save_moving_mask_image(sequence_num, idx, moving_mask_dict, ignored_mask_dict):
    img_path = os.path.join(
        "data_tracking_image_2/training/image_02/", sequence_num, f"{(idx):06d}.png")
    output_path = os.path.join(
        "moving_mask_img_ignored", sequence_num, f"{(idx):06d}.png")
    img = cv2.imread(img_path)
    if idx not in moving_mask_dict[sequence_num]:
        print("the frame {} of sequence {} do not have any moving mask.".format(
            idx, sequence_num))
    else:
        moving_mask = moving_mask_dict[sequence_num][idx]
        color = np.array([0, 255, 0], dtype='uint8')
        masked_img = np.where(moving_mask[..., None], color, img)
        img = cv2.addWeighted(img, 0.8, masked_img, 0.2, 0)

    if idx not in ignored_mask_dict[sequence_num]:
        print("the frame {} of sequence {} do not have any ignored mask.".format(
            idx, sequence_num))
    else:
        ignored_mask = ignored_mask_dict[sequence_num][idx]
        color = np.array([0, 0, 255], dtype='uint8')
        masked_img = np.where(ignored_mask[..., None], color, img)
        img = cv2.addWeighted(img, 0.8, masked_img, 0.2, 0)

    cv2.imwrite(output_path, img)


def save_moving_mask_image_detectron(sequence_num, idx):
    img_path = os.path.join(
        "data_tracking_image_2/training/image_02/", sequence_num, f"{(idx):06d}.png")
    mask_path = os.path.join("moving_mask_detectron",
                             sequence_num, f"{(idx):06d}.npy")
    output_path = os.path.join(
        "moving_mask_img_detectron", sequence_num, f"{(idx):06d}.png")
    img = cv2.imread(img_path)
    try:
        moving_mask = np.load(mask_path)
        color = np.array([0, 255, 0], dtype='uint8')
        masked_img = np.where(moving_mask[..., None], color, img)
        img = cv2.addWeighted(img, 0.8, masked_img, 0.2, 0)

    except:
        print("the frame {} of sequence {} do not have any moving mask.".format(
            idx, sequence_num))

    cv2.imwrite(output_path, img)


def save_seqs_moving_mask_image_detectron(moving_threshold, association_threshold):
    fulltrain = r"fulltrain.seqmap"
    seqmap, max_frames = fmo.SeqmapLoader.load_seqmap(fulltrain)
    label_folder = r"data_tracking_label_2/training/label_02"
    pose_folder = r"orbslam3_poses"
    moving_obj_detector = fmo.MovingObjectDetector(seqmap_filename=fulltrain,
                                                   label_folder=label_folder,
                                                   pose_folder=pose_folder,
                                                   moving_threshold=moving_threshold)
    all_obj_info_dict, all_moving_id_dict = moving_obj_detector.find_all_moving_obj_id()
    detectron_img_folder = {s: os.path.join(
        "mask_from_detectron", s) for s in seqmap}
    da.MovingMaskAssociator.get_moving_mask_dict_detectron(
        all_moving_id_dict, detectron_img_folder, all_obj_info_dict, association_threshold)

    for seq_num, frame_nums in max_frames.items():
        os.makedirs(os.path.join(
            "moving_mask_img_detectron", seq_num), exist_ok=True)
        for frame_num in range(frame_nums+1):
            save_moving_mask_image_detectron(seq_num, frame_num)


def generate_all_videos_from_mask_image_detectron():
    image_root_folder = "moving_mask_img_detectron"
    fulltrain = r"fulltrain.seqmap"
    all_seq, _ = fmo.SeqmapLoader.load_seqmap(fulltrain)
    for seq in all_seq:
        curr_image_folder = os.path.join(image_root_folder, seq)
        output_path = os.path.join("videos_final_detectron", seq+".mp4")
        generate_video_from_image_seq(curr_image_folder, output_path)


if __name__ == "__main__":
    # save_seqs_moving_bbox_image(moving_threshold=-0.2)
    # generate_all_videos_from_bbox_image()
    save_seqs_moving_mask_image_detectron(
        moving_threshold=0.1, association_threshold=0.2)
    # generate_all_videos_from_mask_image_detectron()
