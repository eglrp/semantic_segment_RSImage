#coding:utf-8

import cv2
import numpy as np
import os
import sys
import argparse
# from keras.preprocessing.image import img_to_array
from keras.models import load_model
from sklearn.preprocessing import LabelEncoder
from keras.preprocessing.image import img_to_array

import matplotlib.pyplot as plt

from predict.smooth_tiled_predictions import predict_img_with_smooth_windowing_multiclassbands

from keras import backend as K
K.set_image_dim_ordering('th')
os.environ["CUDA_VISIBLE_DEVICES"] = "2"

# segnet_classes = [0., 1., 2., 3., 4.]
unet_classes = [0., 1., 2.]

labelencoder = LabelEncoder()
labelencoder.fit(unet_classes)

input_image = '../../data/test/1.png'


"""(1.1) for unet road predict"""
unet_model_path = '../../data/models/unet_channel_first_multiclass65536.h5'
unet_output_mask = '../../data/predict/unet/mask_unet_roads_'+os.path.split(input_image)[1]


window_size = 256






def cheap_predict(input_img, model):
    stride = window_size

    h, w, _ = input_img.shape
    print 'h,w:', h, w
    padding_h = (h // stride + 1) * stride
    padding_w = (w // stride + 1) * stride
    padding_img = np.zeros((padding_h, padding_w, 3))
    padding_img[0:h, 0:w, :] = input_img[:, :, :]

    # Using "img_to_array" to convert the dimensions ordering, to adapt "K.set_image_dim_ordering('**') "
    padding_img = img_to_array(padding_img)
    print 'src:', padding_img.shape

    mask_whole = np.zeros((padding_h, padding_w, 3), dtype=np.float32)
    for i in range(padding_h // stride):
        for j in range(padding_w // stride):
            crop = padding_img[:3, i * stride:i * stride + window_size, j * stride:j * stride + window_size]
            # crop = padding_img[i * stride:i * stride + window_size, j * stride:j * stride + window_size, :3]
            cb, ch, cw = crop.shape  # for channel_first

            print ('crop:{}'.format(crop.shape))

            crop = np.expand_dims(crop, axis=0)
            print ('crop:{}'.format(crop.shape))
            pred = model.predict(crop, verbose=2)
            pred = pred[0].reshape(window_size, window_size, 3)
            pred[0, :, :] = 0
            # pred = labelencoder.inverse_transform(pred[0])
            print(np.unique(pred))

            # pred = pred[0,:,:,:]
            print(np.unique(pred))

            mask_whole[i * stride:i * stride + window_size, j * stride:j * stride + window_size, :] = pred[:, :, :]

    outputresult = mask_whole[0:h, 0:w, :] * 255

    # plt.imshow(outputresult[:,:,1])
    plt.imshow(outputresult)
    plt.title("Original predicted result")
    plt.show()


def new_predict_for_unet_multiclass(small_img_patches, model, real_classes,labelencoder):
    """

    :param small_img_patches: input image 4D array (patches, row,column, channels)
    :param model: pretrained model
    :param real_classes: the number of classes and the channels of output mask
    :param labelencoder:
    :return: predict mask 4D array (patches, row,column, real_classes)
    """

    # assert(real_classes ==1 ) # only usefully for one class

    small_img_patches = np.array(small_img_patches)
    print (small_img_patches.shape)
    assert (len(small_img_patches.shape) == 4)

    patches,row,column,input_channels = small_img_patches.shape

    mask_output = []
    for p in range(patches):
        # crop = np.zeros((row, column, input_channels), np.uint8)
        crop = small_img_patches[p,:,:,:]
        crop = img_to_array(crop)
        crop = np.expand_dims(crop, axis=0)
        # print ('crop:{}'.format(crop.shape))
        pred = model.predict(crop, verbose=2)
        pred = pred[0].reshape((row,column,real_classes))

        # 将预测结果2D expand to 3D
        # res_pred = np.expand_dims(pred, axis=-1)

        mask_output.append(pred)

    mask_output = np.array(mask_output)
    print ("Shape of mask_output:{}".format(mask_output.shape))

    return mask_output


if __name__=='__main__':
    input_img = cv2.imread(input_image)
    input_img = np.array(input_img, dtype="float") / 255.0  # must do it
    model = load_model(unet_model_path)

    # cheap_predict(input_img,model)

    predictions_smooth = predict_img_with_smooth_windowing_multiclassbands(
        input_img,
        model,
        window_size=window_size,
        subdivisions=2,
        real_classes=3,  # output channels = 是真的类别,
        pred_func=new_predict_for_unet_multiclass,
        labelencoder=labelencoder
    )
    plt.imshow(predictions_smooth)
    plt.title("Original predicted result")
    plt.show()





