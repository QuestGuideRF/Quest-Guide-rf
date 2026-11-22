import cv2
import numpy as np
import logging
import os
from typing import Tuple
logger =logging .getLogger (__name__ )
class PoseService :
    def __init__ (self ,config ):
        self .config =config
        self .session =None
        self ._init_movenet ()
    def _init_movenet (self ):
        try :
            import onnxruntime as ort
            model_url ="https://github.com/onnx/models/raw/main/vision/body_analysis/movenet/singlepose_lightning_4.onnx"
            model_path ="/tmp/movenet_lightning.onnx"
            if not os .path .exists (model_path ):
                try :
                    import urllib .request
                    logger .info ("Скачиваю MoveNet Lightning ONNX модель...")
                    urllib .request .urlretrieve (model_url ,model_path )
                    logger .info ("✅ Модель скачана")
                except Exception as e :
                    logger .warning (f"Не удалось скачать модель: {e }. Используем упрощённую версию")
                    self .session =None
                    return
            providers =['CPUExecutionProvider']
            sess_options =ort .SessionOptions ()
            sess_options .intra_op_num_threads =1
            sess_options .inter_op_num_threads =1
            self .session =ort .InferenceSession (
            model_path ,
            sess_options =sess_options ,
            providers =providers
            )
            logger .info ("✅ MoveNet Lightning ONNX успешно загружен")
        except ImportError :
            logger .warning ("ONNX Runtime не установлен. Используем упрощённую детекцию")
            self .session =None
        except Exception as e :
            logger .warning (f"Ошибка загрузки MoveNet: {e }. Используем упрощённую детекцию")
            self .session =None
    async def check_pose (self ,photo_path :str ,required_pose :str )->Tuple [bool ,str ]:
        try :
            img =cv2 .imread (photo_path )
            if img is None :
                return False ,"❌ Не удалось прочитать фото"
            h ,w =img .shape [:2 ]
            max_size =1280
            if max (h ,w )>max_size :
                scale =max_size /max (h ,w )
                img =cv2 .resize (img ,(int (w *scale ),int (h *scale )),interpolation =cv2 .INTER_LINEAR )
            hsv =cv2 .cvtColor (img ,cv2 .COLOR_BGR2HSV )
            hist =cv2 .calcHist ([hsv ],[0 ],None ,[180 ],[0 ,180 ])
            unique_hues =np .count_nonzero (hist )
            if unique_hues <30 :
                logger .warning (f"Фото имеет мало уникальных цветов: {unique_hues }")
                return False ,"❌ Фото выглядит как обложка или рисунок. Сделайте реальное фото на телефон."
            if self .session :
                return await self ._check_pose_movenet (img ,required_pose )
            else :
                return await self ._check_pose_simple (img ,required_pose )
        except Exception as e :
            logger .error (f"Ошибка при проверке позы: {e }",exc_info =True )
            return False ,f"❌ Ошибка проверки позы. Попробуйте сделать фото ещё раз."
    async def _check_pose_movenet (self ,img ,required_pose :str )->Tuple [bool ,str ]:
        try :
            input_size =192
            img_resized =cv2 .resize (img ,(input_size ,input_size ))
            img_rgb =cv2 .cvtColor (img_resized ,cv2 .COLOR_BGR2RGB )
            input_data =img_rgb .astype (np .float32 )/255.0
            input_data =np .expand_dims (input_data ,axis =0 )
            input_name =self .session .get_inputs ()[0 ].name
            output_name =self .session .get_outputs ()[0 ].name
            outputs =self .session .run ([output_name ],{input_name :input_data })
            keypoints =outputs [0 ][0 ]
            nose =keypoints [0 ]
            left_shoulder =keypoints [5 ]
            right_shoulder =keypoints [6 ]
            left_elbow =keypoints [7 ]
            right_elbow =keypoints [8 ]
            left_wrist =keypoints [9 ]
            right_wrist =keypoints [10 ]
            min_confidence =0.3
            high_confidence_points =sum (1 for kp in keypoints if kp [2 ]>0.4 )
            if high_confidence_points <8 :
                logger .warning (f"Мало уверенных точек: {high_confidence_points }/17")
                return False ,"❌ Не удалось распознать человека на фото. Убедитесь, что вы полностью видны в кадре."
            if required_pose =="hands_up":
                if left_wrist [2 ]<min_confidence or right_wrist [2 ]<min_confidence :
                    return False ,"❌ Не вижу рук на фото. Поднимите руки выше!"
                if left_shoulder [2 ]<min_confidence or right_shoulder [2 ]<min_confidence :
                    return False ,"❌ Не вижу плечи. Встаньте ближе к камере!"
                left_raised =left_wrist [0 ]<left_shoulder [0 ]
                right_raised =right_wrist [0 ]<right_shoulder [0 ]
                if left_raised and right_raised :
                    return True ,"✅ Руки подняты! Отлично!"
                elif left_raised or right_raised :
                    return False ,"❌ Поднимите обе руки выше над головой!"
                else :
                    return False ,"❌ Поднимите руки выше над головой!"
            elif required_pose =="heart":
                if left_wrist [2 ]<min_confidence or right_wrist [2 ]<min_confidence :
                    return False ,"❌ Не вижу рук. Покажите сердечко руками!"
                if nose [2 ]<min_confidence :
                    return False ,"❌ Не вижу лицо. Встаньте лицом к камере!"
                hands_up =left_wrist [0 ]<nose [0 ]and right_wrist [0 ]<nose [0 ]
                hands_close =abs (left_wrist [1 ]-right_wrist [1 ])<0.15
                if hands_up and hands_close :
                    return True ,"✅ Сердечко получилось! ❤️"
                elif not hands_up :
                    return False ,"❌ Поднимите руки над головой для сердечка!"
                else :
                    return False ,"❌ Сведите руки ближе, чтобы получилось сердечко!"
            elif required_pose =="point":
                if left_wrist [2 ]<min_confidence and right_wrist [2 ]<min_confidence :
                    return False ,"❌ Не вижу рук. Укажите пальцем на объект!"
                left_pointing =(
                left_wrist [2 ]>min_confidence and
                left_elbow [2 ]>min_confidence and
                abs (left_wrist [0 ]-left_elbow [0 ])<0.1
                )
                right_pointing =(
                right_wrist [2 ]>min_confidence and
                right_elbow [2 ]>min_confidence and
                abs (right_wrist [0 ]-right_elbow [0 ])<0.1
                )
                if left_pointing or right_pointing :
                    return True ,"✅ Указываете пальцем! Супер! 👉"
                else :
                    return False ,"❌ Вытяните руку горизонтально и укажите пальцем!"
            return False ,f"❌ Неизвестная поза: {required_pose }. Обратитесь в поддержку."
        except Exception as e :
            logger .error (f"Ошибка MoveNet ONNX: {e }",exc_info =True )
            return False ,f"❌ Ошибка проверки позы. Попробуйте сделать фото ещё раз."
    async def _check_pose_simple (self ,img ,required_pose :str )->Tuple [bool ,str ]:
        try :
            h ,w =img .shape [:2 ]
            max_size =1024
            if max (h ,w )>max_size :
                scale =max_size /max (h ,w )
                new_w =int (w *scale )
                new_h =int (h *scale )
                img =cv2 .resize (img ,(new_w ,new_h ),interpolation =cv2 .INTER_AREA )
            gray =cv2 .cvtColor (img ,cv2 .COLOR_BGR2GRAY )
            face_cascade =cv2 .CascadeClassifier (
            cv2 .data .haarcascades +'haarcascade_frontalface_default.xml'
            )
            faces =face_cascade .detectMultiScale (gray ,scaleFactor =1.3 ,minNeighbors =5 ,minSize =(30 ,30 ))
            if len (faces )==0 :
                return False ,"❌ Не вижу лицо на фото. Встаньте лицом к камере!"
            (face_x ,face_y ,face_w ,face_h )=faces [0 ]
            face_center_y =face_y +face_h //2
            edges =cv2 .Canny (gray ,50 ,150 )
            contours ,_ =cv2 .findContours (edges ,cv2 .RETR_EXTERNAL ,cv2 .CHAIN_APPROX_SIMPLE )
            upper_contours =[
            cnt for cnt in contours
            if cv2 .boundingRect (cnt )[1 ]<face_y and cv2 .contourArea (cnt )>500
            ]
            if required_pose =="hands_up":
                if len (upper_contours )>=2 :
                    return True ,"✅ Руки подняты! Отлично!"
                else :
                    return False ,"❌ Поднимите руки выше над головой!"
            elif required_pose in ["heart","point"]:
                if len (upper_contours )>=1 :
                    return True ,f"✅ Поза принята!"
                else :
                    return False ,f"❌ Покажите руки на фото!"
            return False ,f"❌ Не удалось проверить позу. Попробуйте сделать фото ещё раз."
        except Exception as e :
            logger .error (f"Ошибка упрощённой проверки: {e }",exc_info =True )
            return False ,f"❌ Ошибка проверки позы: {str (e )}. Попробуйте сделать фото ещё раз."
    async def check_people_count (self ,photo_path :str ,min_people :int )->Tuple [bool ,str ]:
        try :
            img =cv2 .imread (photo_path )
            original_h ,original_w =img .shape [:2 ]
            img_area =original_h *original_w
            h ,w =original_h ,original_w
            max_size =1024
            if max (h ,w )>max_size :
                scale =max_size /max (h ,w )
                img =cv2 .resize (img ,(int (w *scale ),int (h *scale )),interpolation =cv2 .INTER_LINEAR )
                h ,w =img .shape [:2 ]
            gray =cv2 .cvtColor (img ,cv2 .COLOR_BGR2GRAY )
            face_cascade =cv2 .CascadeClassifier (
            cv2 .data .haarcascades +'haarcascade_frontalface_default.xml'
            )
            faces =face_cascade .detectMultiScale (
            gray ,
            scaleFactor =1.2 ,
            minNeighbors =8 ,
            minSize =(100 ,100 ),
            maxSize =(400 ,400 )
            )
            valid_faces =[]
            for (x ,y ,fw ,fh )in faces :
                face_area =fw *fh
                scaled_img_area =h *w
                face_ratio =face_area /scaled_img_area
                if 0.02 <=face_ratio <=0.50 :
                    valid_faces .append ((x ,y ,fw ,fh ))
                    logger .debug (f"Валидное лицо: размер {fw }x{fh }, площадь {face_ratio :.2%}")
                else :
                    logger .debug (f"Отфильтровано лицо: размер {fw }x{fh }, площадь {face_ratio :.2%} (не в диапазоне 2-50%)")
            count =len (valid_faces )
            logger .info (f"Обнаружено валидных лиц: {count } (всего детекций: {len (faces )}), требуется: {min_people }")
            if count >=min_people :
                return True ,f"✅ На фото {count } человек(а)!"
            else :
                return False ,f"❌ На фото {count } человек(а), нужно минимум {min_people }"
        except Exception as e :
            logger .error (f"Ошибка при подсчёте людей: {e }",exc_info =True )
            return False ,f"❌ Ошибка проверки количества людей. Попробуйте сделать фото ещё раз."
    def __del__ (self ):
        if self .session :
            del self .session
        logger .info ("PoseService (MoveNet ONNX) очищен")