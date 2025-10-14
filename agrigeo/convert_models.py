from tensorflow.keras.models import load_model
from tensorflow.keras.layers import InputLayer
from tensorflow.keras.utils import custom_object_scope

# Workaround for legacy InputLayer
def legacy_inputlayer(*args, **kwargs):
    if 'batch_shape' in kwargs:
        kwargs.pop('batch_shape')
    return InputLayer(*args, **kwargs)

# Ignore old DTypePolicy references
ignore_dtype_policy = lambda x: None

models = ["Wheat", "Maize", "Tomato"]

for m in models:
    h5_path = rf"agrigeo\models\{m}.h5"
    keras_path = rf"agrigeo\models\{m}.keras"

    print(f"Converting {m}...")

    try:
        with custom_object_scope({
            'InputLayer': legacy_inputlayer,
            'DTypePolicy': ignore_dtype_policy
        }):
            model = load_model(h5_path)
        
        model.save(keras_path)
        print(f"{m} converted successfully!\n")
    except Exception as e:
        print(f"Failed to convert {m}: {e}\n")
