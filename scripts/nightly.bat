@echo off
echo ========================================
echo Steam Price Collector - Nightly Job
echo ========================================
echo Starting at %date% %time%

call conda activate myenv

python -m src.cli nightly-job --regions us cn gb jp de

echo Nightly job completed at %date% %time%
echo ========================================
