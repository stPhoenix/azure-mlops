from collections import namedtuple


ModelMetadata = namedtuple("ModelMetadata", ["name", "version"])
InferenceRequest = namedtuple("InferenceRequest", ["symbol", "start_date", "end_date"])
