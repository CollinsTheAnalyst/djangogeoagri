from keras.models import load_model, Model
from keras.layers import Input
import os

models = ["Wheat", "Maize", "Tomato"]
base_dir = "agrigeo/models"

def load_legacy_model(h5_path):
    # Load the model without compiling (ignore unsupported InputLayer args)
    return load_model(h5_path, compile=False)

def replace_input_layer(model):
    # Grab original input shape from the first layer
    orig_input_shape = model.layers[0].input_shape[1:]  # skip batch dim
    new_input = Input(shape=orig_input_shape)
    # Connect the rest of the model to this new input
    x = new_input
    for layer in model.layers[1:]:
        x = layer(x)
    new_model = Model(new_input, x)
    return new_model

for m in models:
    h5_path = os.path.join(base_dir, f"{m}.h5")
    keras_path = os.path.join(base_dir, f"{m}.keras")
    
    print(f"Converting {m}...")
    try:
        model = load_legacy_model(h5_path)
        model = replace_input_layer(model)
        model.save(keras_path)
        print(f"{m} converted successfully!\n")
    except Exception as e:
        print(f"Failed to convert {m}: {e}\n")
