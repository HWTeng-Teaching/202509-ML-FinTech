
# Imbalance-Aware Feature Selection and Machine Learning for U.S. Corporate Bankruptcy Prediction
**Authors:**
Yun-Chen Li, Rou-Rou Yu, Yi-An Chen, Huei-Wen Tung

<br>

</div>




---

## Abstract

This study explores the application of financial statement features for
predicting the bankruptcy of U.S. companies. Accurate bankruptcy prediction
is vital for investors, financial institutions, and regulators to identify financial
distress early, mitigate potential losses, and maintain market stability. Machine learning techniques are employed to analyze variables derived from firms
balance sheets, income statements, and cash flow statements, capturing their
underlying financial structure and performance. A comprehensive dataset
of publicly listed U.S. firms is used to train and validate predictive models, including Random Forest, Support Vector Machine, Extreme Gradient
Boosting, and Logistic Regression algorithms. The results demonstrate that
financial statement features significantly improve the accuracy of bankruptcy
prediction compared with traditional statistical models (Logistic Regression).
Furthermore, the key financial variables identified by the models provide
valuable insights into the financial health of companies and the early warning
signs of distress. Overall, the findings highlight the potential of integrating
financial statement data and machine learning to enhance corporate failure
prediction and support better investment and risk management decisions.

### Graphic Abstract

![System Architecture and Results](./images/studyplan.png)
*Figure 1: Overview of the data processing pipeline and model architecture.*

This section outlines the structure and contents of the project's main directories and files.

* **README.md**: Include title, authors, abstract.
* **Bankrupty_prediction.pdf**: A PDF export of the main presentation slides.
* **data/**
 below data will be used in EDA_bkypred.ipynb
    * Variable reference.xlsx
    * delisting14-24.csv 
    * link table.xlsx
    * financial statement data yearly [data.csv](https://drive.google.com/file/d/1_BAODv2MkaiXTYAUfelMP2cqoAu9MICe/view?usp=sharing)
* **coding/**
    * **EDA\_bkypred.ipynb**
        * *Exploratory Data Analysis notebook.* Used for initial data cleaning, visualization, and understanding.
    * **test\_benchmark.ipynb**
        * *Benchmark Testing notebook.* Contains the code for setting up and running baseline performance tests.
    * **test\_research\_design.ipynb**
        * *Research Design Testing notebook.* Implements the core experimental methodology and analysis.
    * **summary\_result.ipynb**
        * *Final Summary notebook.* Gathers key results, visualizations, and final conclusions from the project.
        * models.zip are models saved from  **test\_research\_design.ipynb** and respresented in  **summary\_result.ipynb**
          

