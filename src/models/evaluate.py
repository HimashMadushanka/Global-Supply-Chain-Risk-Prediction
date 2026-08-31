from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score
)


def evaluate_model(
    model,
    X,
    y,
    model_name
):

    predictions = model.predict(X)

    probabilities = (
        model.predict_proba(X)[:, 1]
    )

    results = {

        "Model": model_name,

        "Accuracy":
            accuracy_score(
                y,
                predictions
            ),

        "Precision":
            precision_score(
                y,
                predictions,
                zero_division=0
            ),

        "Recall":
            recall_score(
                y,
                predictions,
                zero_division=0
            ),

        "F1_Score":
            f1_score(
                y,
                predictions,
                zero_division=0
            ),

        "ROC_AUC":
            roc_auc_score(
                y,
                probabilities
            )
    }

    return results