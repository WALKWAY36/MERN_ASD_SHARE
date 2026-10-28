"""
Обучение модели на реальном датасете с features из JSON и расширенной визуализацией
"""

import os

import numpy as np
import pandas as pd
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import (
    GridSearchCV,
    RandomizedSearchCV,
    train_test_split,
    cross_val_score,
    StratifiedKFold,
    learning_curve,
)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    precision_recall_curve,
    f1_score,
)
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from pathlib import Path
import sys

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.config import FEATURES_PATH, LABELS_FILE_PATH
from config.settings import GRID_SEARCH, RANDOM_SEARCH


class ASDDatasetTrainer:
    """
    Обучение модели на датасете с JSON признаками
    """

    def __init__(self, annotations_path=LABELS_FILE_PATH, features_dir=FEATURES_PATH):
        self.annotations_path = annotations_path
        self.features_dir = Path(features_dir)
        self.df_annotations = None
        self.X = None
        self.y = None
        self.feature_names = None
        self.video_ids = None

    def load_annotations(self):
        """Загружает аннотации"""
        self.df_annotations = pd.read_csv(self.annotations_path)
        print(f" Загружено аннотаций: {len(self.df_annotations)}")
        print(f"  Класс 0 (норма): {(self.df_annotations['expert_label'] == 0).sum()}")
        print(f"  Класс 1 (РАС): {(self.df_annotations['expert_label'] == 1).sum()}")
        return self.df_annotations

    def parse_additional_features(self, features_str):
        """
        Парсит строку с дополнительными признаками
        """
        if pd.isna(features_str) or features_str == "":
            return {}

        try:
            features = str(features_str).split(";")
            features = [f.strip() for f in features if f.strip()]

            result = {}
            for feature in features:
                result[feature] = 1

            return result
        except:
            return {}

    def extract_features_from_json(self, json_path):
        """
        Извлекает признаки из JSON файла
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        features = {}

        agg = data["aggregated_features"]
        features["total_abrupt_movements"] = agg["total_abrupt_movements"]
        features["movements_per_minute"] = agg["movements_per_minute"]

        for pair, value in agg["symmetry_metrics"].items():
            key = f"symmetry_{pair.replace(' ', '_').replace('_vs_', '_')}"
            features[key] = value

        for body_part, freq_data in agg["frequency_features"].items():
            prefix = body_part.replace(" ", "_").replace("ё", "е")
            features[f"{prefix}_dominant_freq"] = freq_data["dominant_frequency_hz"]
            features[f"{prefix}_freq_range"] = (
                freq_data["frequency_range_hz"][1] - freq_data["frequency_range_hz"][0]
            )

        for body_part, amp_data in agg["amplitude_features"].items():
            prefix = body_part.replace(" ", "_").replace("ё", "е")
            features[f"{prefix}_mean_speed"] = amp_data["mean_speed"]
            features[f"{prefix}_std_speed"] = amp_data["std_speed"]
            features[f"{prefix}_max_speed"] = amp_data["max_speed"]
            features[f"{prefix}_speed_variance"] = amp_data["speed_variance"]

        for body_part, freq in agg["movement_frequency"].items():
            prefix = body_part.replace(" ", "_").replace("ё", "е")
            features[f"{prefix}_movement_freq"] = freq

        quality = data["quality_metrics"]
        features["json_detection_rate"] = quality["detection_rate"]
        features["json_avg_keypoint_confidence"] = quality["avg_keypoint_confidence"]

        features["json_duration_sec"] = data["video_metadata"]["duration_sec"]

        return features

    def prepare_dataset(self):
        """
        Подготавливает датасет из JSON файлов + признаки из labels.csv
        """
        if self.df_annotations is None:
            self.load_annotations()

        features_list = []
        labels = []
        video_ids = []

        for idx, row in self.df_annotations.iterrows():
            video_id = row["video_id"]
            json_path = self.features_dir / f"{video_id}.json"

            if not json_path.exists():
                print(f"! Файл не найден: {json_path}")
                continue

            try:
                features = self.extract_features_from_json(json_path)

                confidence_str = str(row.get("confidence", "medium")).lower()
                confidence_mapping = {"high": 2, "medium": 1, "low": 0}
                features["csv_confidence"] = confidence_mapping.get(confidence_str, 1)

                features["csv_age_months"] = (
                    float(row.get("age_months", 0))
                    if pd.notna(row.get("age_months"))
                    else 0.0
                )

                additional_features = self.parse_additional_features(
                    row.get("additional_features")
                )
                for feature_name, value in additional_features.items():
                    clean_name = f"csv_additional_{feature_name.replace(' ', '_').replace('-', '_').lower()}"
                    features[clean_name] = value

                features_list.append(features)
                labels.append(row["expert_label"])
                video_ids.append(video_id)
            except Exception as e:
                print(f"! Ошибка при обработке {video_id}: {e}")
                continue

        self.X = pd.DataFrame(features_list).fillna(0)
        self.y = np.array(labels)
        self.video_ids = video_ids
        self.feature_names = self.X.columns.tolist()

        print("\n Подготовлен датасет:")
        print(f"  Образцов: {len(self.X)}")
        print(f"  Признаков: {len(self.feature_names)}")
        print(f"  Классы: {np.bincount(self.y)}")

        print("\n Добавлено признаков из labels.csv: 2")
        print("  - csv_confidence (high=2, medium=1, low=0)")
        print("  - csv_age_months (float)")
        print("\nСтатистика по новым признакам:")
        print(
            f"  confidence - mean: {self.X['csv_confidence'].mean():.2f}, std: {self.X['csv_confidence'].std():.2f}"
        )
        print(
            f"  age_months - mean: {self.X['csv_age_months'].mean():.2f}, std: {self.X['csv_age_months'].std():.2f}, range: [{self.X['csv_age_months'].min():.1f}, {self.X['csv_age_months'].max():.1f}]"
        )

        return self.X, self.y

    from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

    def train_model(
        self,
        model_type="random_forest",
        test_size=0.25,
        random_state=42,
        use_grid_search=False,
        search_type="grid",
    ):
        """
        Обучает модель с кросс-валидацией и сохранением истории обучения
        use_grid_search: True для поиска оптимальных параметров
        search_type: 'grid' для GridSearchCV, 'random' для RandomizedSearchCV
        """
        if self.X is None:
            self.prepare_dataset()

        print(f"\n{'=' * 60}")
        print(f"ОБУЧЕНИЕ МОДЕЛИ: {model_type.upper()}")
        print(f"{'=' * 60}")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
            X_scaled,
            self.y,
            self.video_ids,
            test_size=test_size,
            random_state=random_state,
            stratify=self.y,
        )

        print("\nРазделение данных:")
        print(f"  Train: {len(X_train)} образцов")
        print(f"  Test: {len(X_test)} образцов")

        param_grids = {}

        if model_type == "random_forest":
            base_model = RandomForestClassifier(
                random_state=random_state, class_weight="balanced"
            )
            param_grids["grid"] = GRID_SEARCH["RANDOM_FOREST"]
            param_grids["random"] = RANDOM_SEARCH["RANDOM_FOREST"]

        elif model_type == "gradient_boosting":
            base_model = GradientBoostingClassifier(random_state=random_state)
            param_grids["grid"] = GRID_SEARCH["GRADIENT_BOOSTING"]
            param_grids["random"] = RANDOM_SEARCH["GRADIENT_BOOSTING"]

        elif model_type == "mlp":
            base_model = MLPClassifier(
                random_state=random_state,
                early_stopping=True,
                validation_fraction=0.2,
                max_iter=1000,
            )
            param_grids["grid"] = GRID_SEARCH["MLP"]
            param_grids["random"] = RANDOM_SEARCH["MLP"]
        else:
            raise ValueError(f"Неизвестный тип модели: {model_type}")

        if use_grid_search:
            print(f"\nПОИСК ОПТИМАЛЬНЫХ ПАРАМЕТРОВ ({search_type.upper()} SEARCH)...")

            if search_type == "grid":
                search = GridSearchCV(
                    estimator=base_model,
                    param_grid=param_grids["grid"],
                    cv=StratifiedKFold(
                        n_splits=3, shuffle=True, random_state=random_state
                    ),
                    scoring="accuracy",
                    n_jobs=-1,
                    verbose=1,
                )
            elif search_type == "random":
                search = RandomizedSearchCV(
                    estimator=base_model,
                    param_distributions=param_grids["random"],
                    n_iter=20,
                    cv=StratifiedKFold(
                        n_splits=3, shuffle=True, random_state=random_state
                    ),
                    scoring="accuracy",
                    n_jobs=-1,
                    verbose=1,
                    random_state=random_state,
                )
            else:
                raise ValueError(f"Неизвестный тип поиска: {search_type}")

            search.fit(X_train, y_train)

            print("\n! Оптимальные параметры найдены:")
            for param, value in search.best_params_.items():
                print(f"  {param}: {value}")
            print(f"  Лучшая оценка кросс-валидации: {search.best_score_:.4f}")

            model = search.best_estimator_

            search_results = {
                "best_params": search.best_params_,
                "best_score": search.best_score_,
                "cv_results": search.cv_results_,
            }
        else:
            print("\nИспользование базовых параметров модели...")

            if model_type == "random_forest":
                model = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=5,
                    min_samples_split=2,
                    min_samples_leaf=1,
                    random_state=random_state,
                    class_weight="balanced",
                    warm_start=False,
                )
            elif model_type == "gradient_boosting":
                model = GradientBoostingClassifier(
                    n_estimators=200,
                    learning_rate=0.1,
                    max_depth=3,
                    random_state=random_state,
                    min_samples_leaf=1,
                    min_samples_split=5,
                    subsample=0.9,
                )
            elif model_type == "mlp":
                model = MLPClassifier(
                    hidden_layer_sizes=(64, 32),
                    learning_rate_init=0.01,
                    activation="tanh",
                    solver="adam",
                    max_iter=1000,
                    random_state=random_state,
                    early_stopping=True,
                    validation_fraction=0.2,
                )

            search_results = None

        print("\nКросс-валидация (5-fold)...")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        cv_scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy")
        print(f"  CV scores: {cv_scores}")
        print(f"  Mean CV: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

        print("\nВычисление learning curves...")
        train_sizes, train_scores, val_scores = learning_curve(
            model,
            X_train,
            y_train,
            cv=5,
            n_jobs=-1,
            train_sizes=np.linspace(0.1, 1.0, 10),
            scoring="accuracy",
            random_state=random_state,
        )

        print("\nОбучение финальной модели...")
        model.fit(X_train, y_train)

        train_score = model.score(X_train, y_train)
        test_score = model.score(X_test, y_test)

        print("\nТочность:")
        print(f"  Train: {train_score:.3f}")
        print(f"  Test: {test_score:.3f}")

        y_train_pred = model.predict(X_train)
        y_train_proba = model.predict_proba(X_train)[:, 1]
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]

        print(f"\n{'-' * 60}")
        print("CLASSIFICATION REPORT (Test Set):")
        print(f"{'-' * 60}")
        print(
            classification_report(
                y_test, y_pred, target_names=["Норма (0)", "РАС (1)"], digits=3
            )
        )

        print("\nCONFUSION MATRIX:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        print(f"\n  TN={cm[0, 0]}, FP={cm[0, 1]}")
        print(f"  FN={cm[1, 0]}, TP={cm[1, 1]}")

        auc = None
        if len(np.unique(y_test)) > 1:
            auc = roc_auc_score(y_test, y_pred_proba)
            print(f"\nROC AUC: {auc:.3f}")

        f1 = f1_score(y_test, y_pred)
        print(f"F1 Score: {f1:.3f}")

        if hasattr(model, "feature_importances_"):
            print(f"\n{'-' * 60}")
            print("ТОП-15 ВАЖНЫХ ПРИЗНАКОВ:")
            print(f"{'-' * 60}")
            importances = model.feature_importances_
            indices = np.argsort(importances)[::-1][:15]

            for i, idx in enumerate(indices, 1):
                print(f"{i:2d}. {self.feature_names[idx]:40s} {importances[idx]:.4f}")

        print(f"\n{'-' * 60}")
        print("АНАЛИЗ ОШИБОК НА TEST SET:")
        print(f"{'-' * 60}")
        error_count = 0
        for i, (true_label, pred_label, video_id) in enumerate(
            zip(y_test, y_pred, ids_test)
        ):
            if true_label != pred_label:
                proba = y_pred_proba[i]
                print(
                    f"  {video_id}: истинный={true_label}, предсказано={pred_label}, вероятность={proba:.3f}"
                )
                error_count += 1
        print(f"\nВсего ошибок: {error_count}")

        model_data = {
            "model": model,
            "scaler": scaler,
            "feature_names": self.feature_names,
            "model_type": model_type,
            "train_score": train_score,
            "test_score": test_score,
            "cv_scores": cv_scores,
            "auc": auc,
            "f1": f1,
            "learning_curves": {
                "train_sizes": train_sizes,
                "train_scores": train_scores,
                "val_scores": val_scores,
            },
            "search_results": search_results,
            "best_params": search.best_params_ if use_grid_search else None,
        }

        test_data = {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "y_train_pred": y_train_pred,
            "y_train_proba": y_train_proba,
            "y_pred": y_pred,
            "y_pred_proba": y_pred_proba,
            "ids_test": ids_test,
        }

        if use_grid_search:
            model_path = f"trained_model_{model_type}_{search_type}_search.pkl"
        else:
            model_path = f"trained_model_{model_type}.pkl"

        joblib.dump(model_data, model_path)
        print(f"\n✓ Модель сохранена: {model_path}")

        return model_data, test_data

    def compare_hyperparameters(self, model_type="random_forest", random_state=42):
        """
        Сравнивает производительность с разными настройками гиперпараметров
        """
        if self.X is None:
            self.prepare_dataset()

        print(f"\n{'=' * 60}")
        print(f"СРАВНЕНИЕ ГИПЕРПАРАМЕТРОВ ДЛЯ: {model_type.upper()}")
        print(f"{'=' * 60}")

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(self.X)

        X_train, X_test, y_train, y_test, ids_train, ids_test = train_test_split(
            X_scaled,
            self.y,
            self.video_ids,
            test_size=0.25,
            random_state=random_state,
            stratify=self.y,
        )

        results = []

        if model_type == "random_forest":
            param_sets = [
                {
                    "name": "Default",
                    "params": {
                        "n_estimators": 100,
                        "max_depth": 10,
                        "min_samples_split": 5,
                        "min_samples_leaf": 2,
                    },
                },
                {
                    "name": "Simple",
                    "params": {
                        "n_estimators": 50,
                        "max_depth": 5,
                        "min_samples_split": 2,
                        "min_samples_leaf": 1,
                    },
                },
                {
                    "name": "Complex",
                    "params": {
                        "n_estimators": 200,
                        "max_depth": 15,
                        "min_samples_split": 10,
                        "min_samples_leaf": 4,
                    },
                },
            ]

            for param_set in param_sets:
                model = RandomForestClassifier(
                    **param_set["params"],
                    random_state=random_state,
                    class_weight="balanced",
                )

                cv = StratifiedKFold(
                    n_splits=5, shuffle=True, random_state=random_state
                )
                cv_scores = cross_val_score(
                    model, X_train, y_train, cv=cv, scoring="accuracy"
                )

                model.fit(X_train, y_train)
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)

                results.append(
                    {
                        "name": param_set["name"],
                        "params": param_set["params"],
                        "cv_mean": cv_scores.mean(),
                        "cv_std": cv_scores.std(),
                        "train_score": train_score,
                        "test_score": test_score,
                    }
                )

        print("\nРезультаты сравнения:")
        print("-" * 80)
        print(
            f"{'Конфигурация':<15} {'CV Mean':<10} {'CV Std':<10} {'Train':<10} {'Test':<10} {'Params'}"
        )
        print("-" * 80)

        for result in results:
            print(
                f"{result['name']:<15} {result['cv_mean']:.4f}     {result['cv_std']:.4f}     "
                f"{result['train_score']:.4f}     {result['test_score']:.4f}     "
                f"{str(result['params'])[:50]}..."
            )

        fig, axes = plt.subplots(1, 2, figsize=(14, 5))

        names = [r["name"] for r in results]
        cv_means = [r["cv_mean"] for r in results]
        cv_stds = [r["cv_std"] for r in results]

        axes[0].bar(names, cv_means, yerr=cv_stds, capsize=10, alpha=0.7)
        axes[0].set_title("Сравнение кросс-валидации", fontweight="bold")
        axes[0].set_ylabel("Accuracy")
        axes[0].grid(True, alpha=0.3, axis="y")

        train_scores = [r["train_score"] for r in results]
        test_scores = [r["test_score"] for r in results]

        x = np.arange(len(names))
        width = 0.35

        axes[1].bar(x - width / 2, train_scores, width, label="Train", alpha=0.7)
        axes[1].bar(x + width / 2, test_scores, width, label="Test", alpha=0.7)
        axes[1].set_title("Сравнение train/test accuracy", fontweight="bold")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(names)
        axes[1].set_ylabel("Accuracy")
        axes[1].legend()
        axes[1].grid(True, alpha=0.3, axis="y")

        plt.suptitle(
            f"Сравнение гиперпараметров для {model_type.upper()}",
            fontsize=14,
            fontweight="bold",
            y=1.05,
        )
        plt.tight_layout()
        plt.savefig(
            f"hyperparameter_comparison_{model_type}.png", dpi=300, bbox_inches="tight"
        )
        plt.show()

        return results

    def visualize_results(self, model_data, test_data):
        """
        Расширенная визуализация результатов обучения
        """
        y_train = test_data["y_train"]
        y_test = test_data["y_test"]
        y_train_pred = test_data["y_train_pred"]
        y_pred = test_data["y_pred"]
        y_pred_proba = test_data["y_pred_proba"]

        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)

        # 1. Confusion Matrix (Test)
        ax1 = fig.add_subplot(gs[0, 0])
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            ax=ax1,
            xticklabels=["Норма", "РАС"],
            yticklabels=["Норма", "РАС"],
        )
        ax1.set_title("Confusion Matrix (Test)", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Истинный класс")
        ax1.set_xlabel("Предсказанный класс")

        # 2. ROC Curve
        ax2 = fig.add_subplot(gs[0, 1])
        if len(np.unique(y_test)) > 1:
            fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)
            auc = roc_auc_score(y_test, y_pred_proba)

            ax2.plot(
                fpr, tpr, label=f"ROC (AUC = {auc:.3f})", linewidth=2, color="#2E86AB"
            )
            ax2.plot([0, 1], [0, 1], "k--", label="Random", alpha=0.5)
            ax2.set_xlabel("False Positive Rate")
            ax2.set_ylabel("True Positive Rate")
            ax2.set_title("ROC Curve", fontsize=12, fontweight="bold")
            ax2.legend()
            ax2.grid(True, alpha=0.3)

        # 3. Precision-Recall Curve
        ax3 = fig.add_subplot(gs[0, 2])
        if len(np.unique(y_test)) > 1:
            precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
            ax3.plot(recall, precision, linewidth=2, color="#A23B72")
            ax3.set_xlabel("Recall")
            ax3.set_ylabel("Precision")
            ax3.set_title("Precision-Recall Curve", fontsize=12, fontweight="bold")
            ax3.grid(True, alpha=0.3)
            ax3.set_xlim([0, 1])
            ax3.set_ylim([0, 1])

        # # 4. Feature Importance
        # ax4 = fig.add_subplot(gs[1, 0])
        # if hasattr(model, 'feature_importances_'):
        #     importances = model.feature_importances_
        #     indices = np.argsort(importances)[::-1][:15]

        #     colors = plt.cm.viridis(np.linspace(0, 1, 15))
        #     ax4.barh(range(15), importances[indices], color=colors)
        #     ax4.set_yticks(range(15))
        #     ax4.set_yticklabels([self.feature_names[i][:30] for i in indices], fontsize=8)
        #     ax4.set_xlabel('Важность')
        #     ax4.set_title('Топ-15 важных признаков', fontsize=12, fontweight='bold')
        #     ax4.invert_yaxis()

        # # 5. Распределение вероятностей (Test)
        # ax5 = fig.add_subplot(gs[1, 1])
        # ax5.hist(y_pred_proba[y_test == 0], bins=20, alpha=0.6, label='Норма', color='#06D6A0', edgecolor='black')
        # ax5.hist(y_pred_proba[y_test == 1], bins=20, alpha=0.6, label='РАС', color='#EF476F', edgecolor='black')
        # ax5.axvline(x=0.5, color='black', linestyle='--', linewidth=2, label='Порог')
        # ax5.set_xlabel('Вероятность РАС')
        # ax5.set_ylabel('Частота')
        # ax5.set_title('Распределение вероятностей (Test)', fontsize=12, fontweight='bold')
        # ax5.legend()
        # ax5.grid(True, alpha=0.3, axis='y')

        # 6. Learning Curves
        ax6 = fig.add_subplot(gs[1, 0])
        lc = model_data["learning_curves"]
        train_sizes = lc["train_sizes"]
        train_scores_mean = np.mean(lc["train_scores"], axis=1)
        train_scores_std = np.std(lc["train_scores"], axis=1)
        val_scores_mean = np.mean(lc["val_scores"], axis=1)
        val_scores_std = np.std(lc["val_scores"], axis=1)

        ax6.plot(
            train_sizes,
            train_scores_mean,
            "o-",
            color="#2E86AB",
            label="Train",
            linewidth=2,
        )
        ax6.fill_between(
            train_sizes,
            train_scores_mean - train_scores_std,
            train_scores_mean + train_scores_std,
            alpha=0.2,
            color="#2E86AB",
        )
        ax6.plot(
            train_sizes,
            val_scores_mean,
            "o-",
            color="#A23B72",
            label="Validation",
            linewidth=2,
        )
        ax6.fill_between(
            train_sizes,
            val_scores_mean - val_scores_std,
            val_scores_mean + val_scores_std,
            alpha=0.2,
            color="#A23B72",
        )
        ax6.set_xlabel("Размер обучающей выборки")
        ax6.set_ylabel("Accuracy")
        ax6.set_title("Learning Curves", fontsize=12, fontweight="bold")
        ax6.legend()
        ax6.grid(True, alpha=0.3)

        # 7. Cross-Validation Scores
        ax7 = fig.add_subplot(gs[1, 1])
        cv_scores = model_data["cv_scores"]
        folds = np.arange(1, len(cv_scores) + 1)
        colors_cv = plt.cm.Set2(np.linspace(0, 1, len(cv_scores)))
        ax7.bar(folds, cv_scores, color=colors_cv, edgecolor="black", alpha=0.8)
        ax7.axhline(
            y=cv_scores.mean(),
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Mean: {cv_scores.mean():.3f}",
        )
        ax7.set_xlabel("Fold")
        ax7.set_ylabel("Accuracy")
        ax7.set_title("Cross-Validation Scores", fontsize=12, fontweight="bold")
        ax7.set_xticks(folds)
        ax7.legend()
        ax7.grid(True, alpha=0.3, axis="y")

        # # 8. Распределение классов
        # ax8 = fig.add_subplot(gs[2, 1])
        # class_counts = np.bincount(y_test)
        # ax8.bar(['Норма', 'РАС'], class_counts, color=['#06D6A0', '#EF476F'], edgecolor='black', alpha=0.8)
        # ax8.set_ylabel('Количество')
        # ax8.set_title('Распределение классов (Test)', fontsize=12, fontweight='bold')
        # for i, count in enumerate(class_counts):
        #     ax8.text(i, count + 0.5, str(count), ha='center', fontweight='bold')
        # ax8.grid(True, alpha=0.3, axis='y')

        # 9. Calibration Plot
        ax9 = fig.add_subplot(gs[1, 2])
        fraction_of_positives, mean_predicted_value = self._compute_calibration(
            y_test, y_pred_proba, n_bins=10
        )
        ax9.plot(
            mean_predicted_value,
            fraction_of_positives,
            "s-",
            linewidth=2,
            color="#2E86AB",
            label="Model",
        )
        ax9.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
        ax9.set_xlabel("Mean predicted probability")
        ax9.set_ylabel("Fraction of positives")
        ax9.set_title("Calibration Plot", fontsize=12, fontweight="bold")
        ax9.legend()
        ax9.grid(True, alpha=0.3)

        # 10. Ошибки классификации по уверенности
        ax10 = fig.add_subplot(gs[2, 0])
        errors = y_test != y_pred
        correct = ~errors
        ax10.scatter(
            y_pred_proba[correct],
            np.zeros(correct.sum()),
            alpha=0.5,
            c="green",
            label="Correct",
            s=50,
        )
        ax10.scatter(
            y_pred_proba[errors],
            np.ones(errors.sum()),
            alpha=0.5,
            c="red",
            label="Errors",
            s=50,
        )
        ax10.axvline(
            x=0.5, color="black", linestyle="--", linewidth=2, label="Threshold"
        )
        ax10.set_xlabel("Predicted probability")
        ax10.set_yticks([0, 1])
        ax10.set_yticklabels(["Correct", "Error"])
        ax10.set_title(
            "Prediction Confidence vs Errors", fontsize=12, fontweight="bold"
        )
        ax10.legend()
        ax10.grid(True, alpha=0.3, axis="x")

        # 11. Train vs Test Accuracy Comparison
        ax11 = fig.add_subplot(gs[3, 1])
        metrics = ["Accuracy", "Precision", "Recall", "F1-Score"]
        train_metrics = [
            (y_train == y_train_pred).mean(),
            confusion_matrix(y_train, y_train_pred)[1, 1]
            / (
                confusion_matrix(y_train, y_train_pred)[1, 1]
                + confusion_matrix(y_train, y_train_pred)[0, 1]
                + 1e-10
            ),
            confusion_matrix(y_train, y_train_pred)[1, 1]
            / (
                confusion_matrix(y_train, y_train_pred)[1, 1]
                + confusion_matrix(y_train, y_train_pred)[1, 0]
                + 1e-10
            ),
            f1_score(y_train, y_train_pred),
        ]
        test_metrics = [
            (y_test == y_pred).mean(),
            confusion_matrix(y_test, y_pred)[1, 1]
            / (
                confusion_matrix(y_test, y_pred)[1, 1]
                + confusion_matrix(y_test, y_pred)[0, 1]
                + 1e-10
            ),
            confusion_matrix(y_test, y_pred)[1, 1]
            / (
                confusion_matrix(y_test, y_pred)[1, 1]
                + confusion_matrix(y_test, y_pred)[1, 0]
                + 1e-10
            ),
            f1_score(y_test, y_pred),
        ]

        x = np.arange(len(metrics))
        width = 0.35
        ax11.bar(
            x - width / 2,
            train_metrics,
            width,
            label="Train",
            color="#2E86AB",
            alpha=0.8,
            edgecolor="black",
        )
        ax11.bar(
            x + width / 2,
            test_metrics,
            width,
            label="Test",
            color="#A23B72",
            alpha=0.8,
            edgecolor="black",
        )
        ax11.set_ylabel("Score")
        ax11.set_title("Train vs Test Metrics", fontsize=12, fontweight="bold")
        ax11.set_xticks(x)
        ax11.set_xticklabels(metrics, rotation=45, ha="right")
        ax11.legend()
        ax11.grid(True, alpha=0.3, axis="y")
        ax11.set_ylim([0, 1.1])

        # # 12. Threshold Analysis
        # ax12 = fig.add_subplot(gs[3, 2])
        # if len(np.unique(y_test)) > 1:
        #     thresholds_range = np.linspace(0, 1, 100)
        #     accuracies = []
        #     precisions = []
        #     recalls = []
        #     f1_scores = []

        #     for thresh in thresholds_range:
        #         y_pred_thresh = (y_pred_proba >= thresh).astype(int)
        #         accuracies.append((y_test == y_pred_thresh).mean())
        #         cm = confusion_matrix(y_test, y_pred_thresh)
        #         if cm.shape == (2, 2):
        #             precision = cm[1, 1] / (cm[1, 1] + cm[0, 1] + 1e-10)
        #             recall = cm[1, 1] / (cm[1, 1] + cm[1, 0] + 1e-10)
        #             precisions.append(precision)
        #             recalls.append(recall)
        #             f1 = 2 * (precision * recall) / (precision + recall + 1e-10)
        #             f1_scores.append(f1)
        #         else:
        #             precisions.append(0)
        #             recalls.append(0)
        #             f1_scores.append(0)

        #     ax12.plot(thresholds_range, accuracies, label='Accuracy', linewidth=2)
        #     ax12.plot(thresholds_range, precisions, label='Precision', linewidth=2)
        #     ax12.plot(thresholds_range, recalls, label='Recall', linewidth=2)
        #     ax12.plot(thresholds_range, f1_scores, label='F1-Score', linewidth=2)
        #     ax12.axvline(x=0.5, color='black', linestyle='--', alpha=0.5, label='Default threshold')
        #     ax12.set_xlabel('Threshold')
        #     ax12.set_ylabel('Score')
        #     ax12.set_title('Threshold Analysis', fontsize=12, fontweight='bold')
        #     ax12.legend()
        #     ax12.grid(True, alpha=0.3)
        #     ax12.set_ylim([0, 1.05])

        plt.suptitle(
            f"Comprehensive Model Analysis: {model_data['model_type'].upper()}",
            fontsize=16,
            fontweight="bold",
            y=0.995,
        )

        plt.savefig(
            f"training_results_{model_data['model_type']}.png",
            dpi=300,
            bbox_inches="tight",
        )
        print(
            f"\n✓ Визуализация сохранена: training_results_{model_data['model_type']}.png"
        )
        plt.show()

    def _compute_calibration(self, y_true, y_prob, n_bins=10):
        """
        Вычисляет calibration curve для reliability diagram
        """
        bins = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(y_prob, bins) - 1
        bin_indices = np.clip(bin_indices, 0, n_bins - 1)

        fraction_of_positives = np.zeros(n_bins)
        mean_predicted_value = np.zeros(n_bins)

        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() > 0:
                fraction_of_positives[i] = y_true[mask].mean()
                mean_predicted_value[i] = y_prob[mask].mean()
            else:
                fraction_of_positives[i] = np.nan
                mean_predicted_value[i] = np.nan

        valid = ~np.isnan(fraction_of_positives)
        return fraction_of_positives[valid], mean_predicted_value[valid]

    def plot_feature_correlations(self, top_n=20):
        """
        Визуализирует корреляции между топ-N важными признаками
        """
        if self.X is None:
            print("⚠ Датасет не подготовлен. Вызовите prepare_dataset() сначала.")
            return

        try:
            model_data = joblib.load("trained_model_random_forest.pkl")
            if hasattr(model_data["model"], "feature_importances_"):
                importances = model_data["model"].feature_importances_
                indices = np.argsort(importances)[::-1][:top_n]
                top_features = [self.feature_names[i] for i in indices]

                X_top = self.X[top_features]
                corr = X_top.corr()

                fig, ax = plt.subplots(figsize=(14, 12))
                sns.heatmap(
                    corr,
                    annot=True,
                    fmt=".2f",
                    cmap="coolwarm",
                    center=0,
                    square=True,
                    linewidths=1,
                    cbar_kws={"shrink": 0.8},
                    ax=ax,
                    vmin=-1,
                    vmax=1,
                )
                ax.set_title(
                    f"Correlation Matrix of Top {top_n} Features",
                    fontsize=14,
                    fontweight="bold",
                    pad=20,
                )
                plt.xticks(rotation=45, ha="right")
                plt.yticks(rotation=0)
                plt.tight_layout()
                plt.savefig(
                    f"feature_correlations_top{top_n}.png", dpi=300, bbox_inches="tight"
                )
                print(
                    f"\n✓ Correlation matrix сохранена: feature_correlations_top{top_n}.png"
                )
                plt.show()
        except FileNotFoundError:
            print("⚠ Модель не найдена. Обучите модель сначала.")

    def plot_feature_distributions(self, top_n=12):
        """
        Визуализирует распределения топ-N важных признаков по классам
        """
        if self.X is None or self.y is None:
            print("⚠ Датасет не подготовлен. Вызовите prepare_dataset() сначала.")
            return

        try:
            model_data = joblib.load("trained_model_random_forest.pkl")
            if hasattr(model_data["model"], "feature_importances_"):
                importances = model_data["model"].feature_importances_
                indices = np.argsort(importances)[::-1][:top_n]

                fig, axes = plt.subplots(3, 4, figsize=(18, 12))
                axes = axes.flatten()

                for i, idx in enumerate(indices):
                    feature_name = self.feature_names[idx]

                    data_0 = self.X[feature_name][self.y == 0]
                    data_1 = self.X[feature_name][self.y == 1]

                    axes[i].hist(
                        data_0,
                        bins=20,
                        alpha=0.6,
                        label="Норма",
                        color="#06D6A0",
                        edgecolor="black",
                    )
                    axes[i].hist(
                        data_1,
                        bins=20,
                        alpha=0.6,
                        label="РАС",
                        color="#EF476F",
                        edgecolor="black",
                    )

                    axes[i].axvline(
                        data_0.mean(),
                        color="#06D6A0",
                        linestyle="--",
                        linewidth=2,
                        alpha=0.8,
                    )
                    axes[i].axvline(
                        data_1.mean(),
                        color="#EF476F",
                        linestyle="--",
                        linewidth=2,
                        alpha=0.8,
                    )

                    axes[i].set_title(
                        f"{feature_name[:25]}...", fontsize=9, fontweight="bold"
                    )
                    axes[i].set_xlabel("Value", fontsize=8)
                    axes[i].set_ylabel("Frequency", fontsize=8)
                    axes[i].legend(fontsize=7)
                    axes[i].grid(True, alpha=0.3, axis="y")

                plt.suptitle(
                    f"Feature Distributions by Class (Top {top_n})",
                    fontsize=16,
                    fontweight="bold",
                )
                plt.tight_layout()
                plt.savefig(
                    f"feature_distributions_top{top_n}.png",
                    dpi=300,
                    bbox_inches="tight",
                )
                print(
                    f"\n✓ Feature distributions сохранены: feature_distributions_top{top_n}.png"
                )
                plt.show()
        except FileNotFoundError:
            print("⚠ Модель не найдена. Обучите модель сначала.")

    def predict_video(
        self, video_id, json_path, model_path="trained_model_random_forest.pkl"
    ):
        """
        Предсказание для нового видео
        """
        model_data = joblib.load(model_path)
        model = model_data["model"]

        scaler = model_data["scaler"]
        feature_names = model_data["feature_names"]
        print(json_path)
        if not os.path.exists(json_path):
            print("Не найден")
            raise FileNotFoundError(f"Файл не найден: {json_path}")

        features = self.extract_features_from_json(json_path)

        if self.df_annotations is not None:
            row = self.df_annotations[self.df_annotations["video_id"] == video_id]
            if not row.empty:
                row = row.iloc[0]
                confidence_str = str(row.get("confidence", "medium")).lower()
                confidence_mapping = {"high": 2, "medium": 1, "low": 0}
                features["csv_confidence"] = confidence_mapping.get(confidence_str, 1)
                features["csv_age_months"] = row.get("age_months", 0)
                features["csv_preliminary_label"] = row.get("preliminary_label", 0)
                features["csv_agreement"] = row.get("agreement", 0)

                if pd.notna(row.get("additional_features")):
                    try:
                        additional = (
                            json.loads(row["additional_features"])
                            if isinstance(row["additional_features"], str)
                            else row["additional_features"]
                        )
                        if isinstance(additional, dict):
                            for key, value in additional.items():
                                features[f"csv_additional_{key}"] = value
                    except:
                        pass

                features["csv_notes_length"] = (
                    len(str(row.get("notes", ""))) if pd.notna(row.get("notes")) else 0
                )
                features["csv_has_notes"] = (
                    1
                    if pd.notna(row.get("notes")) and len(str(row.get("notes", ""))) > 0
                    else 0
                )
                features["csv_duration_sec"] = row.get("duration_sec", 0)
                features["csv_tracking_quality"] = row.get("tracking_quality", 0)

        X_pred = pd.DataFrame([features])
        print(X_pred)
        for col in feature_names:
            if col not in X_pred.columns:
                X_pred[col] = 0
        X_pred = X_pred[feature_names].fillna(0)

        X_scaled = scaler.transform(X_pred)
        prediction = model.predict(X_scaled)[0]
        probabilities = model.predict_proba(X_scaled)[0]

        result = {
            "video_id": video_id,
            "prediction": "РАС" if prediction == 1 else "Норма",
            "prediction_label": int(prediction),
            "probability_normal": probabilities[0],
            "probability_asd": probabilities[1],
            "confidence": max(probabilities),
        }

        print(f"\nПредсказание для {video_id}:")
        print(f"  Класс: {result['prediction']} ({result['prediction_label']})")
        print(f"  Вероятность нормы: {result['probability_normal']:.3f}")
        print(f"  Вероятность РАС: {result['probability_asd']:.3f}")
        print(f"  Уверенность: {result['confidence']:.3f}")

        return result
