

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from us_visa.pipline.training_pipeline import TrainingPipeline


pipeline = TrainingPipeline()
pipeline.run_pipeline()