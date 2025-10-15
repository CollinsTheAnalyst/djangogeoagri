from tensorflow.keras.models import load_model
from tensorflow.keras.layers import InputLayer
from tensorflow.keras.utils import custom_object_scope

# Workaround for legacy InputLayer
def legacy_inputlayer(*args, **kwargs):
    if 'batch_shape' in kwargs:
        kwargs.pop('batch_shape')
    return InputLayer(*args, **kwargs)

# Minimal dummy class to replace DTypePolicy
class DummyDTypePolicy:
    def __init__(self, *args, **kwargs):
        pass

models = ["Wheat", "Maize", "Tomato"]

for m in models:
    h5_path = rf"agrigeo\models\{m}.h5"
    keras_path = rf"agrigeo\models\{m}.keras"

    print(f"Converting {m}...")

    try:
        with custom_object_scope({
            'InputLayer': legacy_inputlayer,
            'DTypePolicy': DummyDTypePolicy
        }):
            model = load_model(h5_path)
        
        model.save(keras_path)
        print(f"{m} converted successfully!\n")
    except Exception as e:
        print(f"Failed to convert {m}: {e}\n")
