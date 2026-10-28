import logging
import sys

# Настройка логирования В САМОМ НАЧАЛЕ файла
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/app/logs/app.log"),
    ],
)
logger = logging.getLogger(__name__)

# ... остальные импорты ...

try:
    from flask import Flask, request, jsonify
    import traceback
    import os
    from config.config import (
        ANALYZE_MV_CONFIG,
        DATASET_PATH,
        LABELS_FILE_PATH,
        FEATURES_PATH,
        DEFAULT_MODEL,
        MODELS_PATH,
    )
    from core.movement_analyzer import MovementAnalyzer

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    print(f"Ошибка импорта: {e}")

try:
    from core.asdMovementClassifier import ASDDatasetTrainer
except ImportError as e:
    logger.error(f"Ошибка импорта: {e}")
    print(f"Ошибка импорта: {e}")

import threading
import time


app = Flask(__name__)

trainer = None
mv_analyzer = None

analysis_status = {
    "is_analyzing": False,
    "progress": 0,
    "current_video": None,
    "current_user": None,
    "started_at": None,
    "error": None,
    "result": None,
}
analysis_lock = threading.Lock()


def initialize_trainer():
    """Инициализация тренера"""
    global trainer
    if trainer is None:
        try:
            logger.info(f"Инициализация тренера...")
            logger.info(f"LABELS_FILE_PATH: {LABELS_FILE_PATH}")
            logger.info(f"FEATURES_PATH: {FEATURES_PATH}")
            logger.info(f"Файл существует LABELS: {os.path.exists(LABELS_FILE_PATH)}")
            logger.info(
                f"Директория существует FEATURES: {os.path.exists(FEATURES_PATH)}"
            )

            trainer = ASDDatasetTrainer(
                annotations_path=LABELS_FILE_PATH, features_dir=FEATURES_PATH
            )
            logger.info("Тренер успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации тренера: {e}")
            logger.error(traceback.format_exc())
            trainer = None
    return trainer is not None


def initialize_mv_analyzer():
    """Инициализация анализатора движений"""
    global mv_analyzer
    if mv_analyzer is None:
        try:
            logger.info(f"Инициализация MovementAnalyzer...")
            logger.info(f"ANALYZE_MV_CONFIG: {ANALYZE_MV_CONFIG}")
            logger.info(f"DATASET_PATH: {DATASET_PATH}")
            logger.info(f"MODELS_PATH: {MODELS_PATH}")

            mv_analyzer = MovementAnalyzer(ANALYZE_MV_CONFIG)
            logger.info("Анализатор движений успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации анализатора движений: {e}")
            logger.error(traceback.format_exc())
            mv_analyzer = None
    return mv_analyzer is not None


@app.route("/api/mv_analyze", methods=["POST"])
def analyze_movements():
    """Анализ видео и запись статистики в файлы JSON"""

    global analysis_status

    with analysis_lock:
        if analysis_status["is_analyzing"]:
            return jsonify(
                {
                    "error": "Another analysis is already in progress",
                    "current_video": analysis_status["current_video"],
                    "progress": analysis_status["progress"],
                }
            ), 409

        # Блокируем анализ
        analysis_status["is_analyzing"] = True
        analysis_status["progress"] = 0
        analysis_status["error"] = None
        analysis_status["result"] = None
    try:
        logger.info("=== Запрос на анализ движений ===")

        # Проверяем инициализацию
        if not initialize_mv_analyzer():
            logger.error("Анализатор не инициализирован")
            return jsonify({"error": "Movement analyzer initialization failed"}), 500

        data_req = request.get_json()
        logger.info(f"Получены данные: {data_req}")

        if not data_req:
            return jsonify({"error": "No JSON data provided"}), 400

        user_id = data_req.get("user_id")
        video_path = data_req.get("video_path")

        analysis_status["current_video"] = video_path
        analysis_status["current_user"] = user_id
        analysis_status["started_at"] = time.time()

        logger.info(f"user_id: {user_id}")
        logger.info(f"video_path: {video_path}")
        logger.info(f"DATASET_PATH: {DATASET_PATH}")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        if not video_path:
            return jsonify({"error": "video_path is required"}), 400

        if not initialize_mv_analyzer():
            return jsonify({"error": "Movement analyzer initialization failed"}), 500

        # ПРОВЕРЯЕМ СУЩЕСТВОВАНИЕ ФАЙЛОВ И ПУТЕЙ
        outup_dir = os.path.join(DATASET_PATH, user_id) if user_id else DATASET_PATH
        logger.info(f"Выходная директория: {outup_dir}")

        # Проверяем существует ли видео
        if not os.path.exists(video_path):
            logger.error(f"Видео файл не найден: {video_path}")
            return jsonify({"error": f"Video file not found: {video_path}"}), 404

        # Создаем директорию
        os.makedirs(outup_dir, exist_ok=True)
        logger.info(f"Директория создана/существует: {outup_dir}")

        # Анализируем
        analysis_status["progress"] = 5
        logger.info("Запуск анализа...")

        def update_progress(progress_value):
            analysis_status["progress"] = progress_value

        mv_analyzer.set_progress_callback(update_progress)
        dataset_sample = mv_analyzer.export_dataset_sample(
            video_path=video_path, output_dir=outup_dir
        )

        analysis_status["progress"] = 100
        analysis_status["result"] = dataset_sample
        logger.info("Анализ успешно завершен")
        return jsonify(dataset_sample), 200

    except Exception as e:
        logger.error(f"Error during analyze_movements: {str(e)}")
        logger.error(traceback.format_exc())
        analysis_status["error"] = str(e)
        return jsonify(
            {
                "error": f"Internal server error: {str(e)}",
                "traceback": traceback.format_exc(),
            }
        ), 500
    finally:
        # Разблокируем через 2 секунды (чтобы фронтенд успел получить результат)
        def unlock():
            time.sleep(2)
            with analysis_lock:
                analysis_status["is_analyzing"] = False

        threading.Thread(target=unlock, daemon=True).start()


@app.route("/api/mv_analyze/status", methods=["GET"])
def get_analysis_status():
    """Возвращает текущий статус анализа"""
    return jsonify(
        {
            "is_analyzing": analysis_status["is_analyzing"],
            "progress": analysis_status["progress"],
            "current_video": analysis_status["current_video"],
            "current_user": analysis_status["current_user"],
            "started_at": analysis_status["started_at"],
            "error": analysis_status["error"],
            "result": analysis_status["result"]
            if analysis_status["progress"] == 100
            else None,
        }
    )


@app.route("/api/predict", methods=["POST"])
def predict():
    """Обработка запроса на предсказание"""
    try:
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        video_name = data.get("video_name")
        model_path = data.get("model_path")
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        if not video_name:
            return jsonify({"error": "video_name is required"}), 400

        if not model_path:
            model_path = DEFAULT_MODEL

        # Инициализируем тренера если нужно
        if not initialize_trainer():
            return jsonify({"error": "Trainer initialization failed"}), 500

        json_path = os.path.join(
            DATASET_PATH, user_id, "features", f"{video_name}.json"
        )

        # Проверяем существование файла
        if not os.path.exists(json_path):
            return jsonify({"error": f"Features file not found: {json_path}"}), 404

        prediction_result = trainer.predict_video(video_name, json_path, model_path)

        if isinstance(prediction_result, dict) and "prediction" in prediction_result:
            result = {
                "video_id": video_name,
                "prediction": "РАС"
                if prediction_result.get("prediction_label", 0) == 1
                else "Норма",
                "prediction_label": int(prediction_result.get("prediction_label", 0)),
                "probability_normal": float(
                    prediction_result.get("probability_normal", 0)
                ),
                "probability_asd": float(prediction_result.get("probability_asd", 0)),
                "confidence": float(prediction_result.get("confidence", 0)),
            }
        else:
            prediction, probabilities = prediction_result
            result = {
                "video_id": video_name,
                "prediction": "РАС" if prediction == 1 else "Норма",
                "prediction_label": int(prediction),
                "probability_normal": float(probabilities[0]),
                "probability_asd": float(probabilities[1]),
                "confidence": float(max(probabilities)),
            }

        return jsonify(result), 200

    except FileNotFoundError as e:
        return jsonify({"error": f"File not found: {str(e)}"}), 404
    except KeyError as e:
        return jsonify({"error": f"Video not found in dataset: {str(e)}"}), 404
    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route("/api/batch_predict", methods=["POST"])
def batch_predict():
    """Обработка запроса на предсказание для нескольких видео"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        video_names = data.get("video_names", [])
        model_path = data.get("model_path", DEFAULT_MODEL)

        if not video_names:
            return jsonify({"error": "video_names is required"}), 400
        if not isinstance(video_names, list):
            return jsonify({"error": "video_names must be a list"}), 400

        if not initialize_trainer():
            return jsonify({"error": "Trainer initialization failed"}), 500

        results = []
        for video_name in video_names:
            try:
                prediction_result = trainer.predict_video(video_name, model_path)

                if isinstance(prediction_result, dict):
                    result = {
                        "video_id": video_name,
                        "prediction": "РАС"
                        if prediction_result.get("prediction_label", 0) == 1
                        else "Норма",
                        "prediction_label": int(
                            prediction_result.get("prediction_label", 0)
                        ),
                        "probability_normal": float(
                            prediction_result.get("probability_normal", 0)
                        ),
                        "probability_asd": float(
                            prediction_result.get("probability_asd", 0)
                        ),
                        "confidence": float(prediction_result.get("confidence", 0)),
                        "status": "success",
                    }
                else:
                    prediction, probabilities = prediction_result
                    result = {
                        "video_id": video_name,
                        "prediction": "РАС" if prediction == 1 else "Норма",
                        "prediction_label": int(prediction),
                        "probability_normal": float(probabilities[0]),
                        "probability_asd": float(probabilities[1]),
                        "confidence": float(max(probabilities)),
                        "status": "success",
                    }
                results.append(result)
            except Exception as e:
                results.append(
                    {"video_id": video_name, "error": str(e), "status": "error"}
                )

        return jsonify(
            {
                "results": results,
                "total": len(results),
                "successful": sum(1 for r in results if r.get("status") == "success"),
            }
        ), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Запуск сервера...")

    # Предварительная инициализация при запуске
    if initialize_trainer():
        print("Тренер успешно инициализирован")
    else:
        print("Тренер не инициализирован (будет инициализирован при первом запросе)")

    if initialize_mv_analyzer():
        print("Анализатор движений успешно инициализирован")
    else:
        print(
            "Анализатор движений не инициализирован (будет инициализирован при первом запросе)"
        )

    app.run(
        host="0.0.0.0",
        port=5010,
        debug=True,
    )
