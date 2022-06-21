__all__ = (
    'Logger',
)

class Logger():
    
    @staticmethod
    def log(message: str) -> None:
        print('[NORMAL]', message)
    
    @staticmethod
    def debug(message: str) -> None:
        print('[DEBUG]', message)
        
    @staticmethod
    def warn(message: str) -> None:
        print('[WARN]', message)
        
    @staticmethod
    def error(message: str) -> None:
        print('[ERROR]', message)