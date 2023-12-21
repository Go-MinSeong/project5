import cv2
import glob
import logging
import os
import os.path as osp
import torch
import torch.nn.functional as F
# from archs.basicvsrppv2_arch import BasicVSRPlusPlusV2
from archs.psrt_recurrent_arch import BasicRecurrentSwin
from basicsr.data.data_util import read_img_seq
from basicsr.metrics import psnr_ssim
from basicsr.utils import get_root_logger, get_time_str, imwrite, tensor2img
from tqdm import tqdm
import argparse

def main():
    # -------------------- Configurations -------------------- #
    device = torch.device('cuda')
    save_imgs = True
    test_y_channel = False
    crop_border = 0
    # set suitable value to make sure cuda not out of memory
    # interval = 30
    # model
    model_path = 'PSRT_REDS.pth'
    # test data
    test_name = f'100_psrtrecurrent_16f'

    # lr_folder = 'datasets/REDS4/sharp_bicubic'
    # gt_folder = 'datasets/REDS4/GT'
    lr_folder = args.input_path
    gt_folder = args.input_path
    save_folder = args.output_path
    os.makedirs(save_folder, exist_ok=True)

    # logger
    log_file = osp.join(save_folder, f'psnr_ssim_test_{get_time_str()}.log')
    logger = get_root_logger(logger_name='recurrent', log_level=logging.INFO, log_file=log_file)
    logger.info(f'Data: {test_name} - {lr_folder}')
    logger.info(f'Model path: {model_path}')

    # set up the models
    model = BasicRecurrentSwin( mid_channels=64,
                 embed_dim=120,
                 depths=[6, 6, 6],
                 num_heads=[6,6,6],
                 window_size=[3, 8, 8],
                 num_frames=3,
                 cpu_cache_length=100,
                 is_low_res_input=True,
                 spynet_path='experiments/pretrained_models/flownet/spynet_sintel_final-3d2a1287.pth')
    model.load_state_dict(torch.load(model_path)['params'], strict=False)
    model.eval()
    model = model.to(device)

    # avg_psnr_l = []
    # avg_ssim_l = []
    subfolder_l = sorted(glob.glob(osp.join(lr_folder, '*')), key=lambda x: int(x.split("_")[-1]))
    # subfolder_gt_l = sorted(glob.glob(osp.join(gt_folder, '*')))

    # for each subfolder
    subfolder_names = []
    for subfolder in tqdm(subfolder_l[70:]):
        print(subfolder)
        subfolder_name = osp.basename(subfolder)
        subfolder_names.append(subfolder_name)

        # read lq and gt images
        imgs_lq, imgnames = read_img_seq(subfolder, return_imgname=True)

        # calculate the iter numbers
        length = len(imgs_lq)
        # iters = length // interval

        # cluster the excluded file into another group
        # if length % interval > 1:
        #     iters += 1

        # avg_psnr = 0
        # avg_ssim = 0
        # inference
        name_idx = 0
        imgs_lq = imgs_lq.unsqueeze(0).to(device)
        # for i in range(iters):
        #     min_id = min((i + 1) * interval, length)
        #     lq = imgs_lq[:, i * interval:min_id, :, :, :]

        with torch.no_grad():
            outputs = model(imgs_lq).squeeze(0)
        # convert to numpy image
        for idx in range(outputs.shape[0]):
            img_name = imgnames[name_idx] + '.png'
            output = tensor2img(outputs[idx], rgb2bgr=True, min_max=(0, 1))
            # read GT image
            # img_gt = cv2.imread(osp.join(subfolder_gt, img_name), cv2.IMREAD_UNCHANGED)
            # crt_psnr = psnr_ssim.calculate_psnr(
            #     output, img_gt, crop_border=crop_border, test_y_channel=test_y_channel)
            # crt_ssim = psnr_ssim.calculate_ssim(
            # output, img_gt, crop_border=crop_border, test_y_channel=test_y_channel)
            # save
            if save_imgs:
                print(img_name, " save")
                imwrite(output, osp.join(save_folder, f'{img_name}'))
            # avg_psnr += crt_psnr
            # avg_ssim += crt_ssim
            # logger.info(f'{subfolder_name}--{img_name} - PSNR: {crt_psnr:.6f} dB. SSIM: {crt_ssim:.6f}')
            name_idx += 1

        # avg_psnr /= name_idx
        logger.info(f'name_idx:{name_idx}')
        # avg_ssim /= name_idx
        # avg_psnr_l.append(avg_psnr)
        # avg_ssim_l.append(avg_ssim)

    # for folder_idx, subfolder_name in enumerate(subfolder_names):
    #     logger.info(f'Folder {subfolder_name} - Average PSNR: {avg_psnr_l[folder_idx]:.6f} dB. Average SSIM: {avg_ssim_l[folder_idx]:.6f}.')

    # logger.info(f'Average PSNR: {sum(avg_psnr_l) / len(avg_psnr_l):.6f} dB ' f'for {len(subfolder_names)} clips. ')
    # logger.info(f'Average SSIM: {sum(avg_ssim_l) / len(avg_ssim_l):.6f}  '
    # f'for {len(subfolder_names)} clips. ')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_path', type=str, default='', help='choose fuction.')
    parser.add_argument(
        '--output_path', type=str, default='', help='choose fuction.')
    args = parser.parse_args()
    main()
