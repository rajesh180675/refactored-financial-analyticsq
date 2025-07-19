import logging
from financial_analytics_core import (
    DataProcessor as CoreDataProcessor,
    FinancialRatioCalculator,
    PenmanNissimAnalyzer,
    IndustryBenchmarks,
    ChartGenerator
)
from services.analytics_service import AnalyticsService
from services.data_service import DataService
from services.reporting_service import ReportingService


class ComponentFactory:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)

    def create_analytics_service(self) -> AnalyticsService:
        try:
            service = AnalyticsService(self.config, self.state, self.events)
            self.logger.info("Created AnalyticsService")
            return service
        except Exception as e:
            self.logger.error(f"Failed to create AnalyticsService: {e}")
            raise

    def create_data_service(self) -> DataService:
        try:
            service = DataService(self.config, self.state, self.events)
            self.logger.info("Created DataService")
            return service
        except Exception as e:
            self.logger.error(f"Failed to create DataService: {e}")
            raise

    def create_reporting_service(self) -> ReportingService:
        try:
            service = ReportingService(self.config, self.state, self.events)
            self.logger.info("Created ReportingService")
            return service
        except Exception as e:
            self.logger.error(f"Failed to create ReportingService: {e}")
            raise

    def create_core_processor(self) -> CoreDataProcessor:
        try:
            processor = CoreDataProcessor()
            self.logger.info("Created CoreDataProcessor")
            return processor
        except Exception as e:
            self.logger.error(f"Failed to create CoreDataProcessor: {e}")
            raise

    def create_ratio_calculator(self) -> FinancialRatioCalculator:
        try:
            calculator = FinancialRatioCalculator()
            self.logger.info("Created FinancialRatioCalculator")
            return calculator
        except Exception as e:
            self.logger.error(f"Failed to create FinancialRatioCalculator: {e}")
            raise

    def create_penman_nissim_analyzer(self, data, mappings) -> PenmanNissimAnalyzer:
        try:
            analyzer = PenmanNissimAnalyzer(data, mappings)
            self.logger.info("Created PenmanNissimAnalyzer")
            return analyzer
        except Exception as e:
            self.logger.error(f"Failed to create PenmanNissimAnalyzer: {e}")
            raise

    def create_industry_benchmarks(self) -> IndustryBenchmarks:
        try:
            benchmarks = IndustryBenchmarks()
            self.logger.info("Created IndustryBenchmarks")
            return benchmarks
        except Exception as e:
            self.logger.error(f"Failed to create IndustryBenchmarks: {e}")
            raise

    def create_chart_generator(self) -> ChartGenerator:
        try:
            generator = ChartGenerator()
            self.logger.info("Created ChartGenerator")
            return generator
        except Exception as e:
            self.logger.error(f"Failed to create ChartGenerator: {e}")
            raise
