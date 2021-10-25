package LinReg

import breeze.linalg._
import java.io._

object Main {

  def main(args: Array[String]): Unit={

    if (args.length == 1) {
      val dataset = args(0)

      def get_col(myData: Array[Array[String]], colNum: Int): Array[Double] = {
        val dataSize = myData.length
        val outCol = Array.ofDim[Double](dataSize - 1)
        for (i <- 1 until (dataSize - 1)) {
          outCol(i - 1) = myData(i)(colNum).toFloat
        }
        outCol
      }

      val source = scala.io.Source.fromFile("powerplant.csv")
      val data = source.getLines.map(_.split(",")).toArray
      val df = Array.ofDim[Double](data.length - 1, 4)

      for (i <- 1 until data.length - 1; j <- 1 to 4) {
        df(i - 1)(j - 1) = data(i)(j).toDouble
      }

      val X = DenseMatrix(df: _*)
      val target = DenseVector(get_col(data, 5))
      val trainTarget = target(0 until (X.rows * 0.7).toInt)
      val testTarget = target((X.rows * 0.7).toInt until X.rows - 1)

      val train = X(0 until (X.rows * 0.7).toInt, ::)
      val test = X((X.rows * 0.7).toInt until X.rows - 1, ::)
      val trainOnes = DenseMatrix.ones[Double](train.rows, 1)
      val xTrain = DenseMatrix.horzcat(trainOnes, train)
      val testOnes = DenseMatrix.ones[Double](test.rows, 1)
      val xTest = DenseMatrix.horzcat(testOnes, test)

      val moore = (xTrain.t * xTrain) \ xTrain.t

      val weights = moore * trainTarget

      val yPreds = xTest * weights

      val testMSE = sum((testTarget - yPreds) * (testTarget - yPreds)) / yPreds.length

      val predsFile = new PrintWriter(new File("predictions.txt"))
      for (i <- 0 until yPreds.length) {
        predsFile.write(yPreds(i).toString + '\n')
      }
      predsFile.close()

      val mse = new PrintWriter(new File("predictions.txt"))
      mse.write(testMSE.toString)
      mse.close()
    }
    else
      println("No csv file name was given")
  }


}
